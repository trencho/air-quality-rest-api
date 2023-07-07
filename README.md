# Flask RESTful API for training machine learning models used for predicting air quality

# Flask Application Setup Guide

This guide provides step-by-step instructions to set up a Python Flask environment and start a simple Flask application.

## Prerequisites

- Python 3.x installed on your system
- Pip (Python package installer) installed

## Installation Steps

1. Clone the repository or download the source code for your Flask application:  
   git clone https://github.com/trencho/air-quality-rest-api.git
2. Navigate to the project directory:  
   cd air-quality-rest-api
3. Create a virtual environment to isolate the dependencies:  
   python3 -m venv air-quality-rest-api
4. Activate the virtual environment:
    - On macOS and Linux:
      ```
      source air-quality-rest-api/bin/activate
      ```
    - On Windows:
      ```
      air-quality-rest-api\Scripts\activate
      ```
5. Install the required dependencies:
   ```
   pip3 install -r requirements/dev.txt
   ```
6. Set up environment variables if necessary:
    - Define your environment variables in the `.env` file using the `KEY=VALUE` format.
7. Start the Flask application:
   ```
   python src/api/app.py
   ```
   Replace `app.py` with the actual filename of your Flask application's entry point.

8. Open a web browser and visit `http://localhost:5000/api/v1/apidocs` to see your Flask application in action.

## Additional Notes

- If you're deploying your Flask application to a production environment, consult the Flask documentation for
  recommended configuration changes and security measures.
- Remember to deactivate the virtual environment once you're done working on the project:
  deactivate

Congratulations! You have successfully set up a Python Flask environment and started your Flask application. Feel free
to customize and enhance it to meet your specific requirements.

If you have any questions or encounter any issues, please refer to the Flask documentation or seek assistance from the
Python and Flask communities.