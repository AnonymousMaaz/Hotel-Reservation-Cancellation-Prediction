pipeline{
    agent any

    stages{
        stage('Cloning Github Repo to Jenkins'){
            steps{
                script{
                    echo 'Cloning Github Repo to Jenkis'
                    checkout scmGit(branches: [[name: '*/main']], extensions: [], userRemoteConfigs: [[credentialsId: 'github_pat_jenkins', url: 'https://github.com/AnonymousMaaz/Hotel-Reservation-Cancellation-Prediction']])
                }
            }
        }
    }
}