# Nextmv Python TravelTime Routing

Example for running a Python application with TravelTime API integration on the Nextmv Platform.

## Setup

1. Get TravelTime API credentials:
   - Visit [TravelTime API documentation](https://docs.traveltime.com/api/overview/getting-keys)
   - Sign up and get your Application ID and API Key

2. Set environment variables:
   ```bash
   export TT_APP_ID="your_application_id_here"
   export TT_API_KEY="your_api_key_here"
   ```

3. Install packages:
   ```bash
   pip3 install -r requirements.txt
   ```

4. Run the app:
   ```bash
   cat input.json | python3 main.py
   ```

## Next steps

* Open `main.py` and start writing the model.
* Visit our [docs][docs] and [blog][blog]. Need more assistance?
  [Contact][contact] us!

[docs]: https://docs.nextmv.io
[blog]: https://www.nextmv.io/blog
[contact]: https://www.nextmv.io/contact
