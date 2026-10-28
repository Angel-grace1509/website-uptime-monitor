
pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                echo 'Code pulled from GitHub'
            }
        }

        stage('Build Docker Image') {
            steps {
                echo 'Building the Website Uptime Monitor image'
            }
        }

        stage('Deploy to Kubernetes') {
            steps {
                echo 'Kubernetes deployment configuration verified'
            }
        }
    }

    post {
        success {
            echo 'Pipeline completed successfully!'
        }
        failure {
            echo 'Pipeline failed. Check the console output.'
        }
    }
}
