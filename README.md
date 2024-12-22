# Smart LED Lights with Spotify Integration

## Video Demo: CS50X_Presentation.mp4

--- 

This project is a **Flask web application** that integrates smart LED lights with Spotify, allowing users to create a dynamic and immersive lighting experience based on the music they are listening to. Lights are synchronized with the music genres played on Spotify, enhancing the ambiance for every track.

---

## Table of Contents
- [Overview](#overview)
- [Core Structure](#core-structure)
- [Key Features](#key-features)
- [Troubleshooting](#troubleshooting)
- [Security](#security)
- [Disclaimer](#disclaimer)
- [License](#license)
- [Contact](#contact)

---

## Overview
This application provides features such as:
- **User Registration and Login**: Secure user accounts to manage personal preferences.
- **Spotify Integration**: Sync your smart LED lights with music genres detected via Spotify.
- **Light Control via Tuya IoT API**: Adjust light colors and brightness dynamically based on music genres.
- **Music Genre Visualizations**: View insightful graphs of your listening habits with Matplotlib.
- **SQLite Database**: Local storage for user preferences and settings.

---

## Core Structure
- **`app.py`**: The heart of the project. This file manages the Flask session and handles all app logic.  
   To understand its functionality, **read `00_INSTRUCTIONS.html`** in the `instructions` folder.
  
- **Folder Structure**:
  - `static/`: Contains CSS, JavaScript, and images used in the app.
  - `templates/`: Holds HTML files for different routes. The most important file is `index.html`, which serves as the main interface for controlling lights and colors.
  - `instructions/`: Contains documentation, including `00_INSTRUCTIONS.html`.
  - `helpers.py`: Includes utility functions to support `app.py`.
  - `tinyatuya/`: Handles low-level interactions with the Tuya IoT API.
  - `sqlite/`: Stores user data and settings in an SQLite database.
  - `backups/`: Used for saving backup data if necessary.
  - - `00_Spotify_LEDs/`: A zip file containing all the necessary files.

---

## Key Features
- **User Registration and Login**: Secure user authentication system to protect access.
- **Spotify Integration**: Automatically adjusts lights to match the vibe of the current music genre.
- **Light Control**: Manage on/off states, brightness, and colors using the Tuya IoT API.
- **Music Genre-based Lighting**: Example genre mappings:
  - Jazz → Blue or Purple
  - Rock → Red or Orange
  - Classical → White or Soft Yellow
- **Visualization with Matplotlib**: Graphs show genre preferences over time for insights into listening habits.

---

## Troubleshooting
### Spotify Integration Not Working:
- Verify the **Client ID** and **Client Secret** from your Spotify Developer Dashboard.
- Ensure the **Redirect URI** is correctly configured.
- Follow the Spotify API documentation for further help.

### Lights Not Responding:
- Confirm your Tuya API credentials are correct.
- Ensure your LED lights are linked to the Tuya platform.
- Check compatibility with the Tuya SDK.

### Using Multiple Spotify Accounts:
Due to authentication issues, it is currently not possible to use multiple Spotify accounts in the same browser on the same computer.

If you wish to use multiple Spotify accounts in **different browsers** on the same machine, you may encounter fixable issues.  
A possible solution is to uncomment the lines `delete_folder` and `delete_cache` in **`app.py`** at lines **148 and 149**. These functions delete the `flask_session` folder and the associated `.cache`.  

#### Pros:
- This allows multiple Spotify accounts to work simultaneously in different browsers.

#### Cons:
- After logging out, the code will no longer function.  
  You must **restart the code** after each logout to create a new `flask_session` with an associated `.cache`.

---

## Security
### Password Management:
- Passwords are securely hashed and stored in the database.  
  During login, the app compares the hash of the entered password with the stored hash.

### API Keys and Secrets:
- Credentials for Spotify and Tuya are stored for functionality purposes. Due to limitations, **100% security cannot be guaranteed.**

### Data Deletion:
- Users can delete all stored data, including:
  - Login credentials
  - API keys
  - Activity logs

---

## Disclaimer
This application is a **prototype** and may not be fully optimized:
- The design may not be fully responsive on all devices.
- Security measures are basic and may not meet enterprise standards.
- Use at your own discretion.

---

## License
This project is licensed under the MIT License. See the `LICENSE` file for details.

---

## Contact
For questions or feedback, reach out to me at:  
**Email**: [raphael.zaehrer@gmail.com]  
