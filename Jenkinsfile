pipeline{
    agent any
    options {
        skipDefaultCheckout(true)
    }
    environment {
        VENV_DIR = 'venv'
        GCP_PROJECT = "mlops-513607"
        GCLOUD_PATH = "/var/jenkins_home/google-cloud-sdk/bin"
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
        stage('Building and pushing docker image to GCR'){
            steps{
                withCredentials({file(credentialsId: 'gcp_service_json', variable: "GOOGLE_APPLICATION_CREDENTIALS")}){
                    script {
                        echo 'Building and pushing docker image to GCR'
                        sh '''
                        export PATH=$PATH:$(GCLOUD_PATH)

                        gcloud auth activate-service-account --key-file=${GOOGLE_APPLICATION_CREDENTIALS}

                        gcloud config set project ${GCP_PROJECT}

                        gcloud auth configure-docker --quiet

                        docker build -t gcr.io/${GCP_PROJECT}/hotel_reservation_cancellation_prediction:latest .

                        docker push gcr.io/${GCP_PROJECT}/hotel_reservation_cancellation_prediction:latest
                        
                        '''
                    }

                }
            }
        }
    }
}