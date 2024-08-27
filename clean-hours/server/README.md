<!-- GETTING STARTED -->
## Getting Started

The following instructions will guide you through setting up the project on your local machine.

### Prerequisites

1. Python (version 3.11 or higher)
    - Download and install Python from [here](https://www.python.org/downloads/).
        - Ensure that you check the box that says "Add Python to PATH" during installation.
        - Ensure that you check the box that says "Install pip" during installation.
    - Verify installation by running the following command in your terminal:

    ```sh
    python --version        # Check the version of Python
    ```

2. Pip (Python package installer)
    - Verify installation by running the following command in your terminal:

    ```sh
    pip --version       # Check the version of pip
    ```

3. Git (optional, but recommended)
    - Download and install Git from [here](https://git-scm.com/downloads).
    - Verify installation by running the following command in your terminal:

    ```sh
    git --version       # Check the version of Git
    ```

4. VSCode (or any other code editor).
    - Download and install VSCode from [here](https://code.visualstudio.com/).

5. Azure OAI API Key.

### Installation

1. Clone the repo (or download the ZIP file and extract it to a folder on your local machine)

   ```sh
   git clone https://github.com/ChinaiArman/ViveryAIDataTools.git       # Clone the repository
    ```

2. Create a virtual environment

    2.1 Create a virtual environment using the following commands:

    ```sh
    cd clean-hours              # Change to the project directory
    python -m venv .venv        # Create a virtual environment
    ```

    2.2 Activate the virtual environment:
    - Mac:
        - Activation command:

            ```sh
            source .venv/bin/activate     # Activate the virtual environment
            ```

        - Deactivation command:

            ```sh
            source .venv/bin/deactivate       # Deactivate the virtual environment
            ```

    - Windows:
        - Activation command:

            ```sh
            .venv\Scripts\activate.bat        # Activate the virtual environment
            ```

        - Deactivation command:

            ```sh
            .venv\Scripts\deactivate.bat      # Deactivate the virtual environment
            ```

        Your interpreter should now be set to the Virtual Environment instance of python.

3. Install required Python libraries

    ```sh
    cd server                           # Change to the server directory
    pip install -r requirements.txt     # Install the required libraries
    ```

    - If after running the command, none of the packages have installed, restart the terminal and try again, ensuring that the virtual environment is activated.
    - If a single package fails to install, try installing it separately using the following command:

    ```sh
    pip install <package_name>          # Install the package separately
    ```

4. Set up environment variables
    - Create a `.env` file in the server directory of the project.
    - Add the following environment variables to the `.env` file:

    ```sh
    OAI_KEY=""              # Your Azure OAI key
    OAI_BASE=""             # Your Azure OAI base URL
    OAI_ENGINE=""           # Your Azure OAI engine
    ```

<!-- USAGE EXAMPLES -->
## Usage

1. Start the server by running the following command:

    ```sh
    cd ..               # Return to the root directory
    python app.py       # Start the server
    ```

2. Access the API documentation at `http://localhost:5000/` to view the available endpoints and interact with the API.

3. You can also use client software of your choice (cURL, Postman, etc.) to send HTTP requests to the endpoints.
