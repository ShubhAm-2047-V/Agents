from fastapi import FastAPI

app = FastAPI(title='demo_app')

@app.get('/')
def root():
    return {'message': 'Hello from demo_app'}
