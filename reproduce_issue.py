from flask import Flask, render_template
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'test'

# Mock data
traffic_data = {"00:00": 10, "01:00": 5}
history = []
feedback = []

@app.route('/')
def index():
    return render_template('index.html', 
                           traffic_data=traffic_data,
                           prediction=None,
                           probability=None,
                           keywords=[],
                           tags=[],
                           urls=[],
                           history=history,
                           total=0,
                           spam_count=0,
                           ham_count=0,
                           feedback=feedback,
                           radar_data={})

if __name__ == "__main__":
    app.config['SERVER_NAME'] = 'localhost:5000'
    with app.app_context():
        with app.test_request_context():
            try:
                rendered = render_template('index.html', 
                               traffic_data=traffic_data,
                               prediction="",
                               probability="",
                               keywords=[],
                               tags=[],
                               urls=[],
                               history=history,
                               total=0,
                               spam_count=0,
                               ham_count=0,
                               feedback=feedback,
                               radar_data={})
                print("Template rendered successfully.")
                if 'Threat Breakdown' in rendered and 'System Health' in rendered:
                    print("New dashboard elements 'Threat Breakdown' and 'System Health' found.")
                else:
                    print("Missing new dashboard elements.")
                    if 'Threat Breakdown' not in rendered: print("- Threat Breakdown missing")
                    if 'System Health' not in rendered: print("- System Health missing")

                # Verify chart removal
                if 'spamPieChart' in rendered:
                     print("Error: Old chart ID 'spamPieChart' still present.")
                else:
                     print("Old chart ID successfully removed.")
                
                if 'Chart.js' in rendered:
                     print("Error: Chart.js script tag still present.")
                else:
                     print("Chart.js script tag successfully removed.")

                if 'value="Other">Other</option>' in rendered:
                    print("'Other' option found.")
                else:
                    print("'Other' option MISSING.")
                        
            except Exception as e:
                print(f"Error rendering template: {e}")
