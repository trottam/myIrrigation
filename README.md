# My Irrigation - Home Assistant Integration

[![HACS](https://img.shields.io/badge/HACS-Default-orange.svg)](https://hacs.xyz)

My Irrigation is a custom integration for Home Assistant that allows you to control your MySolem irrigation system through Home Assistant. This integration supports controlling the irrigation module and reading its status.

## Features
- Turn on/off irrigation zones.
- Control multiple modules with different configurations (username, password, zone, module ID, serial number).
- Easy setup via Home Assistant Config Flow.

## Installation

### 1. Install via HACS (Home Assistant Community Store)
1. Open Home Assistant and go to **HACS** in the sidebar.
2. Click on the **Frontend** tab.
3. Click on the **Custom repositories** button and add `https://github.com/trottam/myIrrigation` in the repository URL field.
4. Install the integration through the HACS interface.

### 2. Manual Installation
1. Download or clone the repository.
2. Place the `myirrigation` folder in your `custom_components` directory.
   - Your Home Assistant instance directory should look like this: `config/custom_components/myirrigation/`
3. Restart Home Assistant.

## Configuration

Once installed, follow these steps to set up the integration:

1. Go to **Configuration** -> **Integrations** in Home Assistant.
2. Click the **+** button to add a new integration and search for "My Irrigation".
3. Enter the required details (username, password, zone, module ID, and serial number).
4. Click **Submit** and the integration will be added.

## Usage

Once the integration is set up, the irrigation modules will be available as switch entities in Home Assistant. You can control them directly from the Home Assistant UI or automate them using Home Assistant's automation features.

## Troubleshooting

- If the integration is not working, check the Home Assistant logs for errors related to the `myirrigation` component.
- Ensure your MySolem credentials (username, password, and zone) are correctly entered.

## Contributing

Feel free to fork the repository and submit issues or pull requests for improvements!

## License

This project is licensed under the MIT License.
