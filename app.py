from flask import Flask, jsonify, render_template
import serial
import time
import threading
import re

# Configure serial communication
ser = serial.Serial('/dev/ttyUSB0', baudrate=9600, timeout=5)

# Flask app
app = Flask(__name__)

# Global vote counter
votes = {"OptionA": 0, "OptionB": 0}

# Function to send AT commands
def send_command(command, delay=1):
    """Send AT command to SIM800C and get response."""
    ser.write((command + '\r').encode())
    time.sleep(delay)
    response = ser.read(ser.inWaiting()).decode(errors="ignore")
    return response

# Function to read and process SMS
def read_sms():
    """Read unread SMS and update votes."""
    global votes
    send_command('AT+CMGF=1')  # Set SMS mode to text
    sms_list = send_command('AT+CMGL="REC UNREAD"')  # Fetch unread SMS

    # Parse votes from SMS
    for match in re.finditer(r'OptionA|OptionB', sms_list):
        votes[match.group()] += 1

    # Optional: Delete all processed messages
    # Uncomment if needed: send_command('AT+CMGD=1,4')

# Background thread for SMS processing
def sms_polling_thread():
    """Continuously check for new SMS."""
    while True:
        try:
            read_sms()
            time.sleep(10)
        except Exception as e:
            print(f"Error in SMS polling: {e}")

# Start background thread
threading.Thread(target=sms_polling_thread, daemon=True).start()

# Flask routes
@app.route('/')
def index():
    """Render the home page."""
    return render_template('index.html', votes=votes)

@app.route('/api/votes')
def api_votes():
    """Return vote counts as JSON."""
    return jsonify(votes)

@app.route('/api/reset', methods=['POST'])
def reset_votes():
    """Reset the vote counts."""
    global votes
    votes = {"OptionA": 0, "OptionB": 0}
    return jsonify({"message": "Votes reset successfully", "votes": votes})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
