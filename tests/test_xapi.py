import responses
import json
import x_delete_all.xapi as xapi

@responses.activate
def test_list_and_delete(monkeypatch):
    # mock user id
    responses.add(responses.GET, 'https://api.twitter.com/2/users/me', json={'data':{'id':'u1'}}, status=200)
    # mock tweets pages
    responses.add(responses.GET, 'https://api.twitter.com/2/users/u1/tweets', json={'data':[{'id':'t1','text':'a'},{'id':'t2','text':'b'}]}, status=200)
    responses.add(responses.DELETE, 'https://api.twitter.com/2/tweets/t1', status=200)
    responses.add(responses.DELETE, 'https://api.twitter.com/2/tweets/t2', status=200)

    api = xapi.XAPI('BEARER abc')
    uid = api.get_user_id()
    assert uid == 'u1'
    tweets = list(api.list_tweets(uid))
    assert len(tweets) == 2
    assert api.delete_tweet('t1')
    assert api.delete_tweet('t2')
