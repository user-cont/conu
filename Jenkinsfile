#!/usr/bin/env groovy

pipeline {
    agent { label 'userspace-containerization' }
    stages {
        stage('Build') {
            steps {
                sh 'make build-test-container'
            }
        }
        stage('Test'){
            steps {
                sh 'make test'
            }
        }
        stage('Deploy') {
            steps {
                sh 'echo Deploy not implemented'
            }
        }
    }
}
