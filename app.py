from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html', name='World')

@app.route('/ideas')
def ideas():
    return render_template('ideas.html')

@app.route('/timeline')
def timeline():
    return render_template('timeline.html')

@app.route('/projects')
def projects():
    return render_template('projects.html')

@app.route('/ideagen')
def ideagen():
    return render_template('ideagen.html')

if __name__ == '__main__':
    app.run(debug=True)