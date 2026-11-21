pipeline {
    agent any

    environment {
        APP_ENV = 'Devlopment_environment'
        APP_NAME = 'ticketgenie'
    }

    parameters {
        choice(name:'ENVIRONMENT', choices:['DEV', 'STAGING-QA', 'PRODUCTION'], description: 'Choose the correct Enviroment')
        string(name:'VERSION', defaultValue:'1.0', description: 'Version Build')
        booleanParam(name: 'RUN_TESTS', defaultValue: true, description: 'Run Tests?')

    }
    stages {
        stage('build') {
            steps {
                sh "echo Building $APP_NAME version ${params.VERSION} for ${params.ENVIRONMENT}"
                sh 'env | sort'
            }
        }

        stage('test') {
            agent {
                docker { image 'python:3.11-slim' }
            }

            environment {
                APP_ENV = 'qa-techgenie'
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
                    echo Tests-runs: ${params.RUN_TESTS}
                    python -m pytest tests -v --junitxml=test-results.xml
                    echo $APP_ENV
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
                sh "Deploying $APP_NAME version ${params.VERSION} to ${params.ENVIRONMENT}"
            }
        }
    }

    post {
        success { echo 'Pipeline finished successfully!' }
        failure { echo 'Pipeline failed. Check the console output.' }
    }
}