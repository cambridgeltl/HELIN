FROM ubuntu:focal

WORKDIR "/"

# Set the locale
# See https://stackoverflow.com/questions/28405902/how-to-set-the-locale-inside-a-ubuntu-docker-container
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8

# Add Python3.7 repo
RUN apt-get update && apt-get install -y software-properties-common && \ 
    add-apt-repository ppa:deadsnakes/ppa
# Note: this will install Python 3.8, but we need 3.7 for Pytorch


# Install required packages
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    build-essential \
    ca-certificates \
    cmake \
    curl \
    git \
    python3.7 \
    python3.7-dev

# Set Python3.7 as default
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.7 1 && \
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.8 2 && \
    update-alternatives  --set python3 /usr/bin/python3.7


# Install pip
RUN curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py && python3 get-pip.py && \
    rm get-pip.py

# Prepare the environment
COPY requirements.txt /tmp/requirements.txt
RUN bash -c "pip3 install -r /tmp/requirements.txt && \
            rm /tmp/requirements.txt"

# Why these lines? See https://github.com/krallin/tini/issues/8
ENV TINI_VERSION v0.19.0
ADD https://github.com/krallin/tini/releases/download/${TINI_VERSION}/tini /usr/bin/tini
RUN chmod +x /usr/bin/tini
ENTRYPOINT [ "/usr/bin/tini", "--" ]

ARG UNAME=docker-user
ARG GNAME=docker-grp
ARG UID=1000
ARG GID=1000
RUN groupadd -g $GID $GNAME
RUN useradd -m -u $UID -g $GID -s /bin/bash $UNAME

USER $UNAME
WORKDIR /home/$UNAME

CMD ["/bin/bash"]
