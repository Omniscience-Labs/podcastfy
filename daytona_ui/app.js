// Podcastfy Web Interface JavaScript
class PodcastfyUI {
    constructor() {
        this.initializeElements();
        this.bindEvents();
        this.currentAudioUrl = null;
        this.currentTranscript = null;
    }

    initializeElements() {
        // Input elements
        this.urlInput = document.getElementById('urlInput');
        this.textInput = document.getElementById('textInput');
        this.topicInput = document.getElementById('topicInput');
        this.pdfInput = document.getElementById('pdfInput');
        this.imageInput = document.getElementById('imageInput');
        
        // Configuration elements
        this.ttsModel = document.getElementById('ttsModel');
        this.podcastName = document.getElementById('podcastName');
        this.conversationStyle = document.getElementById('conversationStyle');
        this.longForm = document.getElementById('longForm');
        
        // Action elements
        this.generateBtn = document.getElementById('generateBtn');
        this.downloadBtn = document.getElementById('downloadBtn');
        this.shareBtn = document.getElementById('shareBtn');
        this.downloadTranscriptBtn = document.getElementById('downloadTranscriptBtn');
        
        // Display elements
        this.progressSection = document.getElementById('progressSection');
        this.resultsSection = document.getElementById('resultsSection');
        this.errorSection = document.getElementById('errorSection');
        this.progressText = document.getElementById('progressText');
        this.progressBar = document.getElementById('progressBar');
        this.audioPlayer = document.getElementById('audioPlayer');
        this.transcriptContent = document.getElementById('transcriptContent');
        this.errorMessage = document.getElementById('errorMessage');
        
        // File display elements
        this.pdfFiles = document.getElementById('pdfFiles');
        this.imageFiles = document.getElementById('imageFiles');
    }

    bindEvents() {
        // Generate button
        this.generateBtn.addEventListener('click', () => this.generatePodcast());
        
        // File uploads
        this.pdfInput.addEventListener('change', (e) => this.handleFileUpload(e, 'pdf'));
        this.imageInput.addEventListener('change', (e) => this.handleFileUpload(e, 'image'));
        
        // Download buttons
        this.downloadBtn.addEventListener('click', () => this.downloadAudio());
        this.downloadTranscriptBtn.addEventListener('click', () => this.downloadTranscript());
        this.shareBtn.addEventListener('click', () => this.sharePodcast());
    }

    handleFileUpload(event, type) {
        const files = Array.from(event.target.files);
        const displayElement = type === 'pdf' ? this.pdfFiles : this.imageFiles;
        
        if (files.length === 0) return;
        
        const fileList = files.map(file => {
            const size = (file.size / 1024 / 1024).toFixed(2);
            return `<div class="text-green-600"><i class="fas fa-check mr-1"></i>${file.name} (${size}MB)</div>`;
        }).join('');
        
        displayElement.innerHTML = fileList;
    }

    async generatePodcast() {
        try {
            // Validate input
            const hasInput = this.validateInput();
            if (!hasInput) {
                this.showError('Please provide at least one content source (URLs, text, topic, PDF, or images).');
                return;
            }

            // Show progress
            this.showProgress();
            this.hideError();
            this.hideResults();

            // Prepare data
            const requestData = this.prepareRequestData();

            // Make API call
            const response = await this.callPodcastfyAPI(requestData);

            // Handle response
            if (response.success) {
                this.handleSuccess(response);
            } else {
                this.showError(response.error || 'Failed to generate podcast');
            }

        } catch (error) {
            console.error('Error generating podcast:', error);
            this.showError('An error occurred while generating the podcast. Please try again.');
        } finally {
            this.hideProgress();
        }
    }

    validateInput() {
        const urls = this.urlInput.value.trim();
        const text = this.textInput.value.trim();
        const topic = this.topicInput.value.trim();
        const pdfFiles = this.pdfInput.files.length > 0;
        const imageFiles = this.imageInput.files.length > 0;

        return urls || text || topic || pdfFiles || imageFiles;
    }

    prepareRequestData() {
        const data = {
            tts_model: this.ttsModel.value,
            podcast_name: this.podcastName.value || 'PODCASTFY',
            conversation_style: this.conversationStyle.value.split(','),
            longform: this.longForm.checked,
            creativity: 0.7
        };

        // Add content sources
        if (this.urlInput.value.trim()) {
            data.urls = this.urlInput.value.trim().split('\n').filter(url => url.trim());
        }
        
        if (this.textInput.value.trim()) {
            data.text = this.textInput.value.trim();
        }
        
        if (this.topicInput.value.trim()) {
            data.topic = this.topicInput.value.trim();
        }

        // Add files
        if (this.pdfInput.files.length > 0) {
            data.pdf_files = Array.from(this.pdfInput.files);
        }
        
        if (this.imageInput.files.length > 0) {
            data.image_files = Array.from(this.imageInput.files);
        }

        return data;
    }

    async callPodcastfyAPI(data) {
        // For now, we'll simulate the API call
        // In a real implementation, this would call your backend API
        
        return new Promise((resolve) => {
            setTimeout(() => {
                // Simulate successful response
                resolve({
                    success: true,
                    audio_url: '/api/audio/sample.mp3', // This would be the actual audio URL
                    transcript: this.generateSampleTranscript(data),
                    filename: 'podcast_' + Date.now() + '.mp3'
                });
            }, 3000); // Simulate 3-second processing time
        });
    }

    generateSampleTranscript(data) {
        const sources = [];
        if (data.urls) sources.push(`${data.urls.length} website(s)`);
        if (data.text) sources.push('direct text');
        if (data.topic) sources.push(`topic: ${data.topic}`);
        if (data.pdf_files) sources.push(`${data.pdf_files.length} PDF file(s)`);
        if (data.image_files) sources.push(`${data.image_files.length} image(s)`);

        return `<Person1> "Welcome to ${data.podcast_name} - Your Personal Generative AI Podcast! Today we're diving into content from ${sources.join(', ')}."</Person1>

<Person2> "That's right! We've analyzed all the input sources and created an engaging conversation just for you."</Person2>

<Person1> "The content we're covering today includes fascinating insights from multiple sources. Let me break down what we found..."</Person1>

<Person2> "That's really interesting! I particularly noticed how the AI was able to synthesize information from different types of content."</Person2>

<Person1> "Absolutely! This demonstrates the power of multimodal AI processing. Whether it's text, images, or documents, Podcastfy can create meaningful conversations."</Person1>

<Person2> "And the best part is how natural the conversation flows, despite being generated from diverse sources."</Person2>

<Person1> "That's the magic of our conversation generation system. It maintains context and creates engaging dialogue that feels human."</Person1>

<Person2> "Thanks for joining us on this AI-generated podcast journey!"</Person2>`;
    }

    handleSuccess(response) {
        this.currentAudioUrl = response.audio_url;
        this.currentTranscript = response.transcript;
        
        // Update audio player
        this.audioPlayer.src = response.audio_url;
        
        // Update transcript
        this.transcriptContent.innerHTML = this.formatTranscript(response.transcript);
        
        // Show results
        this.showResults();
        
        // Update progress
        this.updateProgress(100, 'Podcast generated successfully!');
    }

    formatTranscript(transcript) {
        return transcript
            .replace(/<Person1>/g, '<div class="mb-2"><strong class="text-blue-600">Person 1:</strong>')
            .replace(/<Person2>/g, '<div class="mb-2"><strong class="text-purple-600">Person 2:</strong>')
            .replace(/<\/Person1>/g, '</div>')
            .replace(/<\/Person2>/g, '</div>');
    }

    showProgress() {
        this.progressSection.classList.remove('hidden');
        this.generateBtn.disabled = true;
        this.generateBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Generating...';
    }

    hideProgress() {
        this.progressSection.classList.add('hidden');
        this.generateBtn.disabled = false;
        this.generateBtn.innerHTML = '<i class="fas fa-magic mr-2"></i>Generate Podcast';
    }

    updateProgress(percentage, text) {
        this.progressBar.style.width = percentage + '%';
        this.progressText.textContent = text;
    }

    showResults() {
        this.resultsSection.classList.remove('hidden');
        this.resultsSection.scrollIntoView({ behavior: 'smooth' });
    }

    hideResults() {
        this.resultsSection.classList.add('hidden');
    }

    showError(message) {
        this.errorMessage.textContent = message;
        this.errorSection.classList.remove('hidden');
        this.errorSection.scrollIntoView({ behavior: 'smooth' });
    }

    hideError() {
        this.errorSection.classList.add('hidden');
    }

    downloadAudio() {
        if (this.currentAudioUrl) {
            const link = document.createElement('a');
            link.href = this.currentAudioUrl;
            link.download = 'podcast.mp3';
            link.click();
        }
    }

    downloadTranscript() {
        if (this.currentTranscript) {
            const blob = new Blob([this.currentTranscript], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = 'transcript.txt';
            link.click();
            URL.revokeObjectURL(url);
        }
    }

    sharePodcast() {
        if (navigator.share && this.currentAudioUrl) {
            navigator.share({
                title: 'My AI-Generated Podcast',
                text: 'Check out this podcast I generated with Podcastfy!',
                url: this.currentAudioUrl
            });
        } else {
            // Fallback: copy URL to clipboard
            navigator.clipboard.writeText(this.currentAudioUrl).then(() => {
                alert('Audio URL copied to clipboard!');
            });
        }
    }
}

// Initialize the UI when the page loads
document.addEventListener('DOMContentLoaded', () => {
    window.podcastfyUI = new PodcastfyUI();
});

// Add some helpful tooltips and validation
document.addEventListener('DOMContentLoaded', () => {
    // Add input validation
    const inputs = document.querySelectorAll('input, textarea, select');
    inputs.forEach(input => {
        input.addEventListener('blur', () => {
            if (input.value.trim() === '' && input.hasAttribute('required')) {
                input.classList.add('border-red-500');
            } else {
                input.classList.remove('border-red-500');
            }
        });
    });

    // Add file size validation
    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(input => {
        input.addEventListener('change', (e) => {
            const files = Array.from(e.target.files);
            const maxSize = 20 * 1024 * 1024; // 20MB
            
            files.forEach(file => {
                if (file.size > maxSize) {
                    alert(`File ${file.name} is too large. Maximum size is 20MB.`);
                    e.target.value = '';
                }
            });
        });
    });
}); 