stage('test') {
    agent {
        docker { image 'python:3.11-slim' }
    }
    steps {
        sh 'python --version'
        sh 'pwd && ls'
    }
}