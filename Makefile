install:
	python -m venv venv
	venv\Scripts\activate && pip install -r requirements.txt
	venv\Scripts\activate && pip install open-clip-torch torch torchvision

run:
	venv\Scripts\activate && flask run --host=0.0.0.0 --port=3000