"""Simple CLI for x-delete-all"""
import argparse
import sys
import webbrowser
import os
from .storage import TokenStore
from .xapi import XAPI
from .db import ArchiveDB
from .auth import AuthManager
import json

def main():
    parser = argparse.ArgumentParser(prog="x-delete-all", description="Local bulk-delete tool for X/Twitter posts")
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("init", help="Initialize local token storage (manual)")
    sub.add_parser("auth", help="Authenticate via OAuth PKCE (recommended)")
    sub.add_parser("fetch", help="Fetch tweets (list)")
    sub.add_parser("dry-run", help="List tweets that WOULD be deleted (no deletes)")
    sub.add_parser("export", help="Export fetched tweets to JSON")
    sub.add_parser("delete", help="Perform deletion of tweets")
    sub.add_parser("resume", help="Resume a previously interrupted delete run")
    sub.add_parser("demo", help="Run a fully-local demo (no network) to try the UI and flows")
    wipe = sub.add_parser("wipe", help="Fetch all tweets and delete them (safe defaults)")
    wipe.add_argument("--yes", action="store_true", help="Skip interactive confirmation and proceed")

    args = parser.parse_args()
    if not args.cmd:
        parser.print_help()
        return

    store = TokenStore()
    db = ArchiveDB()

    if args.cmd == "init":
        password = input("Choose a local password (used to encrypt token): ")
        token = input("Paste your X OAuth2 user token (starts with 'Bearer ' or OAuth2 token): ")
        store.save_token(token.strip(), password)
        print("Token saved encrypted locally.")
        return

    if args.cmd == "auth":
        client_id = input("Enter your X app Client ID (create one at developer portal if needed): ").strip()
        port_in = input("Local callback port [8080]: ").strip()
        port = int(port_in) if port_in else 8080
        auth = AuthManager(client_id=client_id, redirect_port=port)
        token = auth.authenticate()
        if not token:
            print("Authentication failed.")
            return
        # attach client_id so we can refresh later if needed
        token['client_id'] = client_id
        password = input("Choose a local password (used to encrypt token): ")
        store.save_token(token, password)
        print("Token saved encrypted locally.")
        return

    password = input("Enter local password to unlock token: ")
    token = store.load_token(password)
    if not token:
        print("Failed to load token. Run 'init' or 'auth' to store it first.")
        return

    api = XAPI(token)

    if args.cmd == "fetch":
        user_id = api.get_user_id()
        tweets = list(api.list_tweets(user_id))
        print(json.dumps(tweets, indent=2))
        return

    if args.cmd == "dry-run":
        user_id = api.get_user_id()
        tweets = list(api.list_tweets(user_id))
        print(f"{len(tweets)} tweets found.\nSample: \n")
        for t in tweets[:10]:
            print(f"- [{t['id']}] {t.get('text')[:120]}")
        print("\nRun 'export' to save full list or 'delete' to proceed.")
        db.store_fetched(tweets)
        return

    if args.cmd == "demo":
        # Create a fully-local demo dataset so non-technical users can try everything without tokens
        sample = []
        for i in range(1, 21):
            sample.append({'id': f'demo-{i}', 'text': f'Sample demo tweet #{i}', 'created_at': '2026-01-01T00:00:00Z'})
        db.store_fetched(sample)
        print('Demo dataset created with 20 sample tweets.')
        print("Run 'python -m x_delete_all.cli dry-run' to preview, and 'python -m x_delete_all.cli delete' to simulate deletion (will mark as deleted locally). No network calls will be made in demo mode.")
        return

    if args.cmd == "export":
        entries = db.get_fetched()
        if not entries:
            print("No fetched tweets in local archive. Run 'dry-run' first.")
            return
        with open('tweets-export.json','w',encoding='utf-8') as f:
            json.dump(entries, f, ensure_ascii=False, indent=2)
        print("Exported tweets-export.json")
        return

    if args.cmd == "wipe":
        # One-command flow: fetch all tweets (fresh) then delete them. Always write an export backup.
        yes = getattr(args, 'yes', False)
        user_id = api.get_user_id()
        print('Fetching tweets (this may take a while) ...')
        tweets = list(api.list_tweets(user_id, max_results=100000))
        if not tweets:
            print('No tweets found.')
            return
        print(f'Fetched {len(tweets)} tweets. Writing local backup to tweets-export.json')
        with open('tweets-export.json','w',encoding='utf-8') as f:
            json.dump(tweets, f, ensure_ascii=False, indent=2)
        db.store_fetched(tweets)
        if not yes:
            confirm = input("DELETING IS IRREVERSIBLE. Type 'DELETE' to confirm: ")
            if confirm != 'DELETE':
                print('Aborted.')
                return
        else:
            print('Proceeding without interactive confirmation (--yes)')
        # perform deletes
        failures = 0
        for t in tweets:
            if db.is_deleted(t['id']):
                continue
            ok = api.delete_tweet(t['id'])
            if ok:
                db.mark_deleted(t['id'])
                print(f'Deleted: {t['id']}')
            else:
                failures += 1
                print(f'Failed to delete: {t['id']}')
        print('Done. Failures:', failures)
        return

    if args.cmd == "delete":
        confirm = input("DELETING IS IRREVERSIBLE. Type 'DELETE' to confirm: ")
        if confirm != 'DELETE':
            print("Aborted.")
            return
        user_id = api.get_user_id()
        tweets = db.get_fetched()
        if not tweets:
            print("No fetched tweets found locally. Run 'dry-run' first.")
            return
        for t in tweets:
            if db.is_deleted(t['id']):
                continue
            ok = api.delete_tweet(t['id'])
            if ok:
                db.mark_deleted(t['id'])
                print(f"Deleted: {t['id']}")
            else:
                print(f"Failed to delete: {t['id']}")
        print("Done.")
        return

    if args.cmd == "resume":
        # resume uses archived list
        tweets = db.get_fetched()
        for t in tweets:
            if db.is_deleted(t['id']):
                continue
            ok = api.delete_tweet(t['id'])
            if ok:
                db.mark_deleted(t['id'])
                print(f"Deleted: {t['id']}")
            else:
                print(f"Failed to delete: {t['id']}")
        print("Resume complete.")
        return

if __name__ == '__main__':
    main()
