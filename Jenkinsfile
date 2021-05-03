pipeline {
    agent {
        docker {
            image 'edimatt/tox:1.0'
            args ''
            reuseNode true
        }
    }
    stages {
        stage('Integration') {
            steps {
                sh 'tox -e py36'
            }
        }
    }
}

