# Google Colab Setup for QuizGenius

Although this application is built to run perfectly on a local machine, you can also easily execute it directly inside Google Colab, making the application available over the internet via Ngrok.

## Prerequisites
1. Have a Google Account to access Google Colab.
2. Sign up for a free [Ngrok account](https://dashboard.ngrok.com/login) to obtain an Authtoken. Ngrok allows us to expose the Flask development server on Colab to the public internet.

## Instructions

1. Simply upload the `run_colab.ipynb` file to your Google Colab instance. 
2. Zip this entire workspace (`testgenerator`) and upload it to the Colab session filesystem.
3. Over in Colab, the notebook script will automatically unzip the project, install dependencies, and run the server.

Alternatively, you can just execute the notebook as long as the files are uploaded to the root folder `/content/`.

### What the Colab Script Does:
1. **Unzips** your project files.
2. **Installs Requirements**: `pip install -r requirements.txt`
3. **Downloads SpaCy model**: `python -m spacy download en_core_web_sm`
4. **Sets up Ngrok tunneling**: Generates a public URL.
5. **Initializes the DB**: Runs `init_db.py`.
6. **Starts Flask**: Runs `app.py`.

You will see an output like:
```text
* Running on http://127.0.0.1:5000
* NgrokTunnel: "https://<your_ngrok_url>.ngrok-free.app"
```
Click the Ngrok link to view the app!
