FROM reszelaz/sardana-test

EXPOSE 8888
EXPOSE 8050

COPY ./ ./
RUN chmod +x ./docker/demo.sh

ENV SARDANA_JUPYTER_CONF=/docker/demo-sardana-jupyter.yml
ENV TANGO_HOST=localhost:10000

# Where Jupyter-Dash litens on 
ENV HOST=0.0.0.0

# Setup
RUN apt update
RUN apt install -y git
RUN git clone https://gitlab.com/sardana-org/sardana --depth 1

# Install & setup anaconda
RUN apt install wget
RUN wget https://repo.anaconda.com/archive/Anaconda3-2021.11-Linux-x86_64.sh -O ~/anaconda.sh
RUN bash ~/anaconda.sh -b -p $HOME/anaconda

# Setup the environment
RUN $HOME/anaconda/bin/conda env create -f ./docker/demo-environment.yml 
# Install Sardana Kernel
RUN $HOME/anaconda/bin/conda run --no-capture-output -n sardana-jupyter jupyter kernelspec install $PWD/sardana_kernel --user 
# Build Jupyter Lab because of Jupyter Dash
RUN $HOME/anaconda/bin/conda run --no-capture-output -n sardana-jupyter jupyter lab build

WORKDIR /

# Run Jupyter & Sardana
CMD /docker/demo.sh
