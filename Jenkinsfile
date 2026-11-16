pipeline{
    agent any
    options {
        skipDefaultCheckout(true)
    }
    environment {
        VENV_DIR = 'venv'
    }
    stages{
        stage('Cloning Github Repo to Jenkins'){
            steps{
                script{
                    echo 'Cloning Github Repo to Jenkins'
                    checkout scmGit(branches: [[name: '*/main']], extensions: [], userRemoteConfigs: [[credentialsId: 'github_pat_jenkins', url: 'https://github.com/AnonymousMaaz/Hotel-Reservation-Cancellation-Prediction']])
                }
            }
        }
        stage('Setting Up our virtual environment and installing dependencies.'){
            steps{
                script{
                    echo 'Setting Up our virtual environment and installing dependencies.'
                    sh '''
                    python -m venv ${VENV_DIR}
                    . ${VENV_DIR}/bin/activate
                    pip install --upgrade pip
                    pip install -e .
                    '''
                }
            }
        }
    }
}