# Smart LED Lights with Spotify Integration

This project is a Flask web application that integrates smart LED lights with Spotify, allowing users to control their lighting experience based on the music they are listening to. By synchronizing lights with the music genres played on Spotify, this application creates a dynamic and immersive atmosphere. The app provides features like user registration, Spotify integration, smart LED light control via the Tuya IoT API, and a backend powered by SQLite for user preferences.

## Key Features

- **User Registration and Login**: Users can securely create an account, log in, and manage their personal settings. User authentication ensures only authorized access to the app's features.
- **Spotify Integration**: The app connects to the Spotify API, allowing users to sync their smart LED lights with the music playing on Spotify. Lights will change dynamically based on the genre of the current track.
- **LED Light Control**: The application allows users to control their smart LED lights using the Tuya API. It supports basic functions like turning the lights on or off and adjusting color and brightness.
- **Music Genre-based Light Control**: The app listens to the current genre of music playing on Spotify and adjusts the color of the lights accordingly. For instance, if a jazz track is playing, the lights may shift to a cool blue, while a pop song could trigger warmer colors.
- **SQLite Database**: The app uses SQLite to store user data, preferences, and settings locally. This lightweight database ensures fast access and persistence of user preferences across sessions.
- **Matplotlib Visualizations**: The app includes a feature that allows users to visualize their music genre preferences over time with graphs. This feature uses Matplotlib to generate insightful visualizations that reflect the user’s listening habits.

## Requirements

Before you begin, ensure that your system meets the following requirements to run this application:

- **Python 3.x**: The project is built with Python 3.x. You can download it from [python.org](https://www.python.org/downloads/).
- **Flask**: A lightweight WSGI web application framework for Python. It is used for creating the server and handling HTTP requests.
- **SQLite**: A relational database management system used to store user data and preferences.
- **Tuya IoT SDK**: The Tuya SDK is used to interact with Tuya-compatible smart LED lights.
- **Spotify Developer Account**: You will need a Spotify Developer account to access the Spotify API and integrate music features.
- **Matplotlib**: A Python plotting library used to create visualizations.

## Usage

### 1. User Registration and Login
Upon visiting the app's homepage, users will be prompted to register or log in. A secure authentication system is implemented, ensuring that only authorized users can access their settings and preferences.

### 2. Connect to Spotify
After logging in, users will need to connect their Spotify account by granting the app permission to access their Spotify data. This connection enables the application to detect the genre of the currently playing track and adjust the lights accordingly.

### 3. LED Light Control
The app provides controls to turn the LED lights on and off, adjust brightness, and change colors. These controls are powered by the Tuya IoT SDK, and users can set up their smart LED lights in the Tuya app beforehand.

### 4. Automatic Genre-based Light Adjustment
As users listen to music on Spotify, the app detects the genre of the current track and adjusts the lights' color to match the vibe. For instance:
- **Jazz**: Lights may turn blue or purple.
- **Rock**: Lights may turn red or orange.
- **Classical**: Lights could shift to white or soft yellow.

### 5. Visualization of Music Genre Preferences
The app includes a feature that allows users to view a graph of their music genre preferences over time, powered by Matplotlib. This helps users visually understand which genres they listen to most often.

### Troubleshooting

#### Spotify Integration not Working:
- Ensure you have correctly entered the **Client ID** and **Client Secret** for your Spotify Developer account.
- Verify that you have correctly configured the **Redirect URI** settings in your Spotify Developer Dashboard.
- Double-check that the authentication flow is being handled properly within your application.
- If the issue persists, refer to the [Spotify API documentation](https://developer.spotify.com/documentation/web-api/) for further troubleshooting steps.

#### Lights Not Responding:
- Make sure you've read the **"Get Started"** guide on Tuya’s platform thoroughly, ensuring the correct **region**, **device_id**, and other configurations are set up.
- Ensure that your smart LED lights are properly linked to the **SmartIndustry** app and Tuya cloud.
- Verify that your Tuya API credentials are correct and that the lights are compatible with the Tuya SDK.

## Security

#### Password Management
- User passwords are **never stored directly**. Instead, only hashed versions of the passwords are saved in the database using a secure hashing algorithm.
- During login, the application compares the hash of the entered password with the stored hash to verify user credentials.

#### API Keys and Secrets
- **Spotify Client Secret** and **Tuya API credentials** are stored in the database for functionality purposes. However, due to the limitations of this implementation, **100% security cannot be guaranteed**. 
- Users who are uncomfortable with this setup are advised **not to use this program**.

#### Data Deletion
- A dedicated function is implemented to allow users to delete all their data from the application. This includes:
  - Login credentials.
  - API keys and secrets.
  - Any activity logs or traces stored in the database.
- This ensures that users can remove all personal information and credentials securely if they choose to stop using the application.

#### Disclaimer
This application is a prototype and may not provide an optimal user experience. The **front-end design is not fully responsive**, which may affect usability on different devices such as mobile phones or tablets. Additionally, while every effort has been made to ensure security and functionality, users should exercise caution and use the program only if they are comfortable with the described limitations and security measures.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgements

- **Flask**: The web framework used for building the app.
- **Spotify API**: For providing the API that allows music genre synchronization.
- **Tuya IoT SDK**: For enabling smart LED light control.
- **Matplotlib**: Used for creating visualizations of music genre preferences.

## Contact

If you have any questions or feedback about the project, feel free to reach out to me at [raphael.zaehrer@gmail.com].
