FROM reszelaz/sardana-test

EXPOSE 8889

COPY ./ ./
RUN chmod +x ./docker/demo.sh

ENV SARDANA_JUPYTER_CONF=/docker/demo-sardana-jupyter.yml
ENV TANGO_HOST=localhost:10000

# Setup
RUN apt update
RUN apt install -y git
RUN git clone https://github.com/reszelaz/sardana --branch jupyter-ms
RUN git clone https://gitlab.com/taurus-org/taurus

# Install & setup anaconda
RUN apt install wget
RUN wget https://repo.anaconda.com/archive/Anaconda3-2021.05-Linux-x86_64.sh -O ~/anaconda.sh
RUN bash ~/anaconda.sh -b -p $HOME/anaconda

# Setup the environment
RUN $HOME/anaconda/bin/conda env create -f ./docker/demo-environment.yml 
# Install Sardana Kernel
RUN $HOME/anaconda/bin/conda run --no-capture-output -n sardana-jupyter jupyter kernelspec install $PWD/sardana_kernel --user 
# Run Jupyter & Sardana
CMD ./docker/demo.sh
