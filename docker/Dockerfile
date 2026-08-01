FROM pytorch/pytorch:2.3.1-cuda12.1-cudnn8-devel

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
	&& apt-get install -y --no-install-recommends \
		libgl1 \
		ffmpeg \
		libsm6 \
		libxext6 \
		pandoc \
		texlive-xetex \
		lmodern \
	&& rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /tmp/requirements.txt

RUN python -m pip install --upgrade pip \
	&& pip install --no-cache-dir -r /tmp/requirements.txt

RUN mkdir -p /.cache /.local \
	&& chmod -R 777 /.cache /.local

ENV PYTHONUNBUFFERED=1 \
	PYTHONDONTWRITEBYTECODE=1

CMD ["bash"]