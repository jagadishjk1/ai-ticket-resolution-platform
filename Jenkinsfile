pipeline {
    agent any

    environment {
        APP_ENV = 'ticketgenie'
    }

    stages {
        stage('build') {
            steps {
                sh 'Building ${APP_ENV}, build number ${BUILD_NUMBER}'
                sh 'env | sort'
            }
        }

        stage('test') {
            agent {
                docker { image 'python:3.11-slim' }
            }

            environment {
                APP_ENV = 'qa'
            }
            steps {
                sh '''
                    pwd && ls -l
                    cd backend
                    python -m venv .venv
                    . .venv/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements-dev.txt
                    pip list
                    python -m pytest tests -v --junitxml=test-results.xml
                    echo '${APP_ENV}'
                '''
            }
            post { 
                always { 
                    junit 'backend/test-results.xml'
                    } 
                }
        }

        stage('deploy') {
            steps {
                echo "Deploying the application in ${APP_ENV}"
            }
        }
    }

    post {
        success { echo 'Pipeline finished successfully!' }
        failure { echo 'Pipeline failed. Check the console output.' }
    }
}