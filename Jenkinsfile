
pipeline {
    agent any

    options {
        skipDefaultCheckout(true)
    }

    environment {
        VENV_DIR = 'venv'
        GCP_PROJECT = 'mlops-513607'
        GCLOUD_PATH = '/var/jenkins_home/google-cloud-sdk/bin'
    }

    stages {
        stage('Cloning Github Repo to Jenkins') {
            steps {
                echo 'Cloning Github Repo to Jenkins'

                checkout scmGit(
                    branches: [[name: '*/main']],
                    extensions: [],
                    userRemoteConfigs: [[
                        credentialsId: 'github_pat_jenkins',
                        url: 'https://github.com/AnonymousMaaz/Hotel-Reservation-Cancellation-Prediction'
                    ]]
                )
            }
        }

        stage('Setting Up Virtual Environment') {
            steps {
                sh '''
                    set -e

                    python -m venv "${VENV_DIR}"
                    . "${VENV_DIR}/bin/activate"

                    python -m pip install --upgrade pip
                    python -m pip install -e .
                '''
            }
        }

        stage('Building and Pushing Docker Image') {
            steps {
                withCredentials([
                    file(
                        credentialsId: 'gcp_service_json',
                        variable: 'GOOGLE_APPLICATION_CREDENTIALS'
                    )
                ]) {
                    script {
                        echo 'Building and pushing Docker image'

                        sh '''
                            set -e

                            export PATH="${GCLOUD_PATH}:$PATH"

                            gcloud --version
                            docker --version

                            gcloud auth activate-service-account \
                                --key-file="${GOOGLE_APPLICATION_CREDENTIALS}"

                            gcloud config set project "${GCP_PROJECT}"

                            gcloud auth configure-docker --quiet

                            docker build \
                                -t "gcr.io/${GCP_PROJECT}/hotel_reservation_cancellation_prediction:latest" .

                            docker push \
                                "gcr.io/${GCP_PROJECT}/hotel_reservation_cancellation_prediction:latest"
                        '''
                    }
                }
            }
        }
        stage('Deploying to Google Cloud Run') {
            steps {
                withCredentials([
                    file(
                        credentialsId: 'gcp_service_json',
                        variable: 'GOOGLE_APPLICATION_CREDENTIALS'
                    )
                ]) {
                    script {
                        echo 'Deploying to Google Cloud Run'

                        sh '''
                            set -e

                            export PATH="${GCLOUD_PATH}:$PATH"

                            gcloud --version
                            docker --version

                            gcloud auth activate-service-account \
                                --key-file="${GOOGLE_APPLICATION_CREDENTIALS}"

                            gcloud config set project "${GCP_PROJECT}"

                            gcloud run deploy hotel_reservation_cancellation_prediction \
                                --image="gcr.io/${GCP_PROJECT}/hotel_reservation_cancellation_prediction:latest" \
                                --platform=managed \
                                --region=us-central1 \
                                --allow-unauthenticated
                        '''
                    }
                }
            }
        }
    }
}
