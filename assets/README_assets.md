Icons and assets

Replace the placeholder icon.svg with platform-appropriate artwork before building installers.

- icon.svg: simple vector used in packaged builds as a fallback.
- For Windows builds, provide a .ico file and update scripts/build_pyinstaller.sh to reference it via --icon.
- For macOS app bundles, include a .icns file and update packaging accordingly.

This project includes a placeholder so CI and local builds pick up a valid asset path.