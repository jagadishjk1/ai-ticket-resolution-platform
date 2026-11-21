pipeline {
    agent any

    environment {
        APP_ENV = 'Devlopment_environment'
        APP_NAME = 'ticketgenie'
        RAG=credentials('demo-registry')
    }

    parameters {
        choice(name:'ENVIRONMENT', choices:['DEV', 'STAGING-QA', 'PRODUCTION'], description: 'Choose the correct Enviroment')
        string(name:'VERSION', defaultValue:'1.0', description: 'Version Build')
        booleanParam(name: 'RUN_TESTS', defaultValue: true, description: 'Run Tests?')

    }
    stages {

        stage('secrets-demo') {
            sh 'echo Username: $RAG_USR'
            sh 'echo Password: $RAG_PSW'

            withCredentials([string(credentialsId: 'demo-api-key', variable: 'TOKEN')]) {
                sh 'echo using the token'
            }
        }


        stage('build') {
            steps {
                sh "echo Building $APP_NAME version ${params.VERSION} for ${params.ENVIRONMENT}"
            }
        }

        stage('test') {
            when {
                    beforeAgent true
                    expression { params.RUN_TESTS }
            }

            agent {
                docker { image 'python:3.11-slim' }
            }

            environment {
                APP_ENV = 'qa-techgenie'
            }
            steps {
                sh "echo Tests-runs: ${params.RUN_TESTS}"
                sh '''
                    pwd && ls -l
                    cd backend
                    python -m venv .venv
                    . .venv/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements-dev.txt
                    pip list
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

        stage('smoke-check') {
            when {
                beforeAgent true
                expression { params.ENVIRONMENT in ['STAGING-QA', 'PRODUCTION'] }          
            }
            
            agent {
                docker { image 'python:3.11-slim' }
            }

            environment {
                APP_ENV = 'qa-techgenie'
            }
            steps {
                sh '''
                    cd backend
                    python -m venv .venv
                    . .venv/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements-dev.txt
                    pip list
                    python -m pytest tests -v --junitxml=test-results.xml
                    echo $APP_ENV
                '''
            }
        }

        stage('deploy') {
            steps {
                sh "echo Deploying $APP_NAME version ${params.VERSION} to ${params.ENVIRONMENT}"
            }
        }
    }

    post {
        success { echo 'Pipeline finished successfully!' }
        failure { echo 'Pipeline failed. Check the console output.' }
    }
}