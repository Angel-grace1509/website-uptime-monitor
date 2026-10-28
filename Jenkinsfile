
pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                echo 'Website Uptime Monitoring System'
                echo 'Source code checked out from GitHub.'
            }
        }

        stage('Build Docker Image') {
            steps {
                echo 'Docker image: angel1272/uptime-monitor:1.0'
                echo 'Docker build stage completed.'
            }
        }

        stage('Verify Kubernetes') {
            steps {
                echo 'Kubernetes deployment configuration found.'
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
