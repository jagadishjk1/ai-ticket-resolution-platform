pipeline {
    agent any
    
    environment {
        APP_ENV = 'Devlopment_environment'
    }

    stages {
        stage ('build') {
            steps {
            echo "Building application in ${APP_ENV}"
            }
        }

        stage ('test') {
            steps {
                echo "Testing the application in ${APP_ENV}"
            }
        }

        stage ('deploy') {
            steps {
                echo "Deploying the application in ${APP_ENV}"
            }
        }
    }
    post {
        success {
            echo 'Pipeline finished successfully!'
        }
        failure {
            echo 'Pipeline failed. Check the console output.'
        }
    }
}