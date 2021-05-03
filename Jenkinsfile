pipeline {
    agent {
        docker {
            image 'edimatt/tox'
            args ''
            reuseNode true
        }
    }
    stages {
        stage('Integration') {
            steps {
                sh 'tox'
            }
        }
    }
}

