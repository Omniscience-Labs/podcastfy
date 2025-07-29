// Podcastfy Web Interface JavaScript
class PodcastfyUI {
    constructor() {
        this.initializeElements();
        this.bindEvents();
        this.currentAudioUrl = null;
        this.currentTranscript = null;
        // API base URL - updated to point to the correct Render backend
        this.API_BASE_URL = 'https://podcastfy-8x6a.onrender.com';
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
                await this.handleSuccess(response);
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
        try {
            // Create FormData for file uploads
            const formData = new FormData();
            
            // Add JSON data
            const jsonData = { ...data };
            
            // Remove files from JSON data and add to FormData
            if (data.pdf_files) {
                data.pdf_files.forEach(file => {
                    formData.append('pdf_files', file);
                });
                delete jsonData.pdf_files;
            }
            
            if (data.image_files) {
                data.image_files.forEach(file => {
                    formData.append('image_files', file);
                });
                delete jsonData.image_files;
            }
            
            // Add JSON data as a string
            formData.append('data', JSON.stringify(jsonData));
            
            // Make the API call to Render backend
            const response = await fetch(`${this.API_BASE_URL}/api/generate`, {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `HTTP ${response.status}: ${response.statusText}`);
            }
            
            const result = await response.json();
            return result;
            
        } catch (error) {
            console.error('API call failed:', error);
            throw error;
        }
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

    async handleSuccess(response) {
        this.currentAudioUrl = response.audio_url;
        
        // Fetch transcript content
        try {
            const transcriptResponse = await fetch(response.transcript_url);
            if (transcriptResponse.ok) {
                this.currentTranscript = await transcriptResponse.text();
                this.transcriptContent.innerHTML = this.formatTranscript(this.currentTranscript);
            } else {
                console.error('Failed to fetch transcript');
                this.transcriptContent.innerHTML = '<p class="text-red-500">Failed to load transcript</p>';
            }
        } catch (error) {
            console.error('Error fetching transcript:', error);
            this.transcriptContent.innerHTML = '<p class="text-red-500">Failed to load transcript</p>';
        }
        
        // Update audio player
        this.audioPlayer.src = response.audio_url;
        
        // Show results
        this.showResults();
        
        // Update progress
        this.updateProgress(100, 'Podcast generated successfully!');
    }

    showProgress() {
        this.progressSection.style.display = 'block';
        this.updateProgress(0, 'Initializing...');
    }

    hideProgress() {
        this.progressSection.style.display = 'none';
    }

    updateProgress(percentage, text) {
        this.progressBar.style.width = `${percentage}%`;
        this.progressText.textContent = text;
    }

    showResults() {
        this.resultsSection.style.display = 'block';
    }

    hideResults() {
        this.resultsSection.style.display = 'none';
    }

    showError(message) {
        this.errorMessage.textContent = message;
        this.errorSection.style.display = 'block';
    }

    hideError() {
        this.errorSection.style.display = 'none';
    }

    downloadAudio() {
        if (this.currentAudioUrl) {
            const a = document.createElement('a');
            a.href = this.currentAudioUrl;
            a.download = 'podcast.mp3';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
        }
    }

    downloadTranscript() {
        if (this.currentTranscript) {
            const blob = new Blob([this.currentTranscript], { type: 'text/plain' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'transcript.txt';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
        }
    }

    sharePodcast() {
        if (this.currentAudioUrl) {
            if (navigator.share) {
                navigator.share({
                    title: 'Generated Podcast',
                    text: 'Check out this AI-generated podcast!',
                    url: this.currentAudioUrl
                });
            } else {
                // Fallback: copy URL to clipboard
                navigator.clipboard.writeText(this.currentAudioUrl).then(() => {
                    alert('Podcast URL copied to clipboard!');
                });
            }
        }
    }

    formatTranscript(transcript) {
        return transcript.replace(/<Person(\d+)>/g, '<span class="font-bold text-blue-600">Person $1:</span>');
    }
}

// Initialize the UI when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new PodcastfyUI();
});
