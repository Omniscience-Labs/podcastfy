// Podcastfy Web Interface JavaScript
class PodcastfyUI {
    constructor() {
        this.initializeElements();
        this.bindEvents();
        this.currentAudioUrl = null;
        this.currentTranscript = null;
        // API base URL - point to your Render backend
        this.API_BASE_URL = 'https://podcastfy-omni.onrender.com';
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
        
        // Transcript elements
        this.copyTranscriptBtn = document.getElementById('copyTranscriptBtn');
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
        this.copyTranscriptBtn.addEventListener('click', () => this.copyTranscript());
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
            // Prepare JSON data for FastAPI backend
            const requestData = { ...data };
            
            // Note: File uploads not supported in this version - FastAPI backend expects JSON only
            if (data.pdf_files) {
                console.warn('PDF file uploads not supported with FastAPI backend');
                delete requestData.pdf_files;
            }
            
            if (data.image_files) {
                console.warn('Image file uploads not supported with FastAPI backend');
                delete requestData.image_files;
            }
            
            // Make the API call to Render FastAPI backend
            const response = await fetch(`${this.API_BASE_URL}/generate`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestData)
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
        // Handle absolute vs relative URLs
        if (response.audio_url.startsWith('/')) {
            this.currentAudioUrl = `${this.API_BASE_URL}${response.audio_url}`;
        } else {
            this.currentAudioUrl = response.audio_url;
        }
        
        // Handle transcript - Now guaranteed to be available
        if (response.transcript) {
            // Transcript is included directly in the response
            this.currentTranscript = response.transcript;
            this.transcriptContent.innerHTML = this.formatTranscript(this.currentTranscript);
            
            // Store transcript URL if available for direct download
            if (response.transcript_url) {
                this.currentTranscriptUrl = response.transcript_url.startsWith('/') 
                    ? `${this.API_BASE_URL}${response.transcript_url}`
                    : response.transcript_url;
            }
            
            // Show success message for transcript availability
            this.updateTranscriptStatus('✅ Transcript available');
        } else if (response.transcript_url) {
            // Transcript is provided as URL
            try {
                const transcriptUrl = response.transcript_url.startsWith('/') 
                    ? `${this.API_BASE_URL}${response.transcript_url}`
                    : response.transcript_url;
                    
                this.currentTranscriptUrl = transcriptUrl;
                    
                const transcriptResponse = await fetch(transcriptUrl);
                if (transcriptResponse.ok) {
                    this.currentTranscript = await transcriptResponse.text();
                    this.transcriptContent.innerHTML = this.formatTranscript(this.currentTranscript);
                    this.updateTranscriptStatus('✅ Transcript loaded');
                } else {
                    console.error('Failed to fetch transcript');
                    this.transcriptContent.innerHTML = '<p class="text-red-500">Failed to load transcript from server</p>';
                    this.updateTranscriptStatus('❌ Transcript load failed');
                }
            } catch (error) {
                console.error('Error fetching transcript:', error);
                this.transcriptContent.innerHTML = '<p class="text-red-500">Error loading transcript</p>';
                this.updateTranscriptStatus('❌ Transcript error');
            }
        } else {
            // This should now be rare with our improvements
            this.transcriptContent.innerHTML = '<p class="text-amber-600">⚠️ Transcript was not generated with this podcast</p>';
            this.currentTranscript = null;
            this.updateTranscriptStatus('⚠️ No transcript');
        }
        
        // Update audio player with error handling
        this.audioPlayer.src = this.currentAudioUrl;
        
        // Add error handling for audio player
        this.audioPlayer.onerror = () => {
            const errorDiv = this.audioPlayer.parentNode;
            errorDiv.innerHTML = `
                <div class="bg-red-50 border border-red-200 rounded-lg p-4 text-center">
                    <i class="fas fa-exclamation-triangle text-red-500 text-2xl mb-2"></i>
                    <h4 class="font-semibold text-red-800 mb-2">Audio File Not Available</h4>
                    <p class="text-red-700 text-sm mb-3">
                        The audio file is no longer available on the server. This can happen after server restarts.
                    </p>
                    <button onclick="window.location.reload()" 
                            class="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 mr-2">
                        <i class="fas fa-redo mr-1"></i>Regenerate Podcast
                    </button>
                    <button onclick="navigator.clipboard.writeText('${this.currentAudioUrl}')" 
                            class="bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700">
                        <i class="fas fa-copy mr-1"></i>Copy Link Anyway
                    </button>
                </div>
            `;
        };
        
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

    showSuccess(message) {
        // Create success notification if it doesn't exist
        let successSection = document.getElementById('successSection');
        if (!successSection) {
            successSection = document.createElement('div');
            successSection.id = 'successSection';
            successSection.className = 'hidden bg-green-50 border border-green-200 rounded-lg p-4 mb-8';
            successSection.innerHTML = `
                <div class="flex items-center">
                    <i class="fas fa-check-circle text-green-500 mr-2"></i>
                    <span id="successMessage" class="text-green-700"></span>
                </div>
            `;
            this.errorSection.parentNode.insertBefore(successSection, this.errorSection);
        }
        
        const successMessage = document.getElementById('successMessage');
        successMessage.textContent = message;
        successSection.style.display = 'block';
        
        // Auto-hide after 3 seconds
        setTimeout(() => {
            successSection.style.display = 'none';
        }, 3000);
    }

    showShareModal(shareText, audioUrl, podcastName) {
        // Create modal HTML
        const modalHtml = `
            <div id="shareModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" onclick="this.remove()">
                <div class="bg-white rounded-lg p-6 max-w-md w-full mx-4" onclick="event.stopPropagation()">
                    <div class="flex items-center justify-between mb-4">
                        <h3 class="text-lg font-semibold text-gray-800">
                            <i class="fas fa-share mr-2"></i>Share Your Podcast
                        </h3>
                        <button onclick="document.getElementById('shareModal').remove()" class="text-gray-400 hover:text-gray-600">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                    
                    <div class="space-y-4">
                        <!-- Direct Audio Link -->
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-2">
                                🎵 Direct Audio Link
                            </label>
                            <div class="flex">
                                <input type="text" value="${audioUrl}" readonly 
                                       class="flex-1 px-3 py-2 border border-gray-300 rounded-l-md bg-gray-50 text-sm">
                                <button onclick="this.copyToClipboard('${audioUrl}', 'Audio link')" 
                                        class="px-3 py-2 bg-blue-500 text-white rounded-r-md hover:bg-blue-600">
                                    <i class="fas fa-copy"></i>
                                </button>
                            </div>
                            <div class="mt-1 text-xs text-orange-600 link-status">
                                ⚠️ This link is temporary and may expire after server restarts
                            </div>
                        </div>
                        
                        <!-- Full Share Message -->
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-2">
                                💬 Complete Share Message
                            </label>
                            <textarea readonly class="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50 text-sm h-20">${shareText}</textarea>
                            <button onclick="this.copyToClipboard(\`${shareText}\`, 'Share message')" 
                                    class="mt-2 w-full px-4 py-2 bg-green-500 text-white rounded-md hover:bg-green-600">
                                <i class="fas fa-copy mr-1"></i>Copy Full Message
                            </button>
                        </div>
                        
                        <!-- Best Practices Info -->
                        <div class="bg-blue-50 border border-blue-200 rounded-md p-3 text-sm">
                            <h4 class="font-medium text-blue-800 mb-1">📱 Best Sharing Practices:</h4>
                            <ul class="text-blue-700 text-xs space-y-1">
                                <li>• For permanent sharing: Use "Download & Share" to send the actual file</li>
                                <li>• For quick sharing: Copy the direct link (may expire later)</li>
                                <li>• Include regeneration instructions for recipients</li>
                            </ul>
                        </div>
                        
                        <!-- Quick Share Options -->
                        <div class="grid grid-cols-2 gap-2">
                            <button onclick="this.shareViaEmail('${podcastName}', '${audioUrl}')" 
                                    class="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700">
                                <i class="fas fa-envelope mr-1"></i>Email Link
                            </button>
                            <button onclick="this.downloadAndShare('${audioUrl}', '${podcastName}')" 
                                    class="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700">
                                <i class="fas fa-download mr-1"></i>Download & Share
                            </button>
                        </div>
                        
                        <!-- Regeneration Instructions -->
                        <div class="bg-amber-50 border border-amber-200 rounded-md p-3 text-xs">
                            <h4 class="font-medium text-amber-800 mb-1">🔄 If Link Stops Working:</h4>
                            <p class="text-amber-700">
                                Share this regeneration guide: Visit <strong>${window.location.origin}</strong>, 
                                enter the same content/topic, and generate a new podcast.
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Add modal to page
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        // Add methods to modal buttons
        const modal = document.getElementById('shareModal');
        modal.copyToClipboard = (text, type) => {
            navigator.clipboard.writeText(text).then(() => {
                this.showSuccess(`${type} copied to clipboard!`);
            });
        };
        
        modal.shareViaEmail = (title, url) => {
            const subject = encodeURIComponent(`🎙️ ${title} - AI Generated Podcast`);
            const body = encodeURIComponent(`Hi!\n\nI created this podcast using AI and wanted to share it with you:\n\n"${title}"\n\n🎵 Listen here: ${url}\n\n⚠️ Note: This link provides direct audio download. If the link doesn't work (files are temporary), you can regenerate the podcast at:\n${window.location.origin}\n\n✨ Created with Podcastfy - AI Podcast Generator`);
            window.open(`mailto:?subject=${subject}&body=${body}`);
        };
        
        modal.downloadAndShare = async (url, name) => {
            // Trigger download first
            await this.downloadAudio();
            // Show instructions
            this.showSuccess('Podcast downloaded! You can now attach the file to emails or messages.');
            modal.remove();
        };
        
        // Test if the audio link is still working
        modal.testAudioLink = async (url) => {
            try {
                const response = await fetch(url, { method: 'HEAD' });
                return response.ok;
            } catch (error) {
                return false;
            }
        };
        
        // Add real-time link status checking
        modal.testAudioLink(audioUrl).then(isWorking => {
            const linkStatus = modal.querySelector('.link-status');
            if (linkStatus) {
                if (isWorking) {
                    linkStatus.innerHTML = '<span class="text-green-600">✅ Link is currently working</span>';
                } else {
                    linkStatus.innerHTML = '<span class="text-red-600">❌ Link may not be working - consider downloading instead</span>';
                }
            }
        });
    }

    async downloadAudio() {
        if (this.currentAudioUrl) {
            try {
                // Show download progress
                const originalBtn = this.downloadBtn;
                const originalText = originalBtn.innerHTML;
                originalBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-1"></i>Downloading...';
                originalBtn.disabled = true;

                // Generate a better filename with timestamp
                const now = new Date();
                const timestamp = now.toISOString().slice(0, 19).replace(/[:]/g, '-');
                const podcastName = this.podcastName.value || 'Podcastfy';
                const filename = `${podcastName}-${timestamp}.mp3`;

                // For cross-origin downloads, we need to fetch and create blob
                const response = await fetch(this.currentAudioUrl);
                if (!response.ok) throw new Error('Download failed');
                
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                
                const a = document.createElement('a');
                a.href = url;
                a.download = filename;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);

                // Show success message
                this.showSuccess('Podcast downloaded successfully!');

                // Reset button
                originalBtn.innerHTML = originalText;
                originalBtn.disabled = false;
            } catch (error) {
                console.error('Download failed:', error);
                this.showError('Download failed. Please try again.');
                
                // Reset button
                this.downloadBtn.innerHTML = '<i class="fas fa-download mr-1"></i>Download MP3';
                this.downloadBtn.disabled = false;
            }
        }
    }

    downloadTranscript() {
        if (this.currentTranscript) {
            // Generate a better filename with timestamp
            const now = new Date();
            const timestamp = now.toISOString().slice(0, 19).replace(/[:]/g, '-');
            const podcastName = this.podcastName.value || 'Podcastfy';
            const filename = `${podcastName}-transcript-${timestamp}.txt`;
            
            const blob = new Blob([this.currentTranscript], { type: 'text/plain' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            
            this.showSuccess('Transcript downloaded successfully!');
        }
    }

    copyTranscript() {
        if (this.currentTranscript) {
            navigator.clipboard.writeText(this.currentTranscript).then(() => {
                this.showSuccess('Transcript copied to clipboard!');
            }).catch(err => {
                console.error('Failed to copy transcript:', err);
                this.showError('Failed to copy transcript to clipboard');
            });
        }
    }

    async sharePodcast() {
        if (this.currentAudioUrl) {
            const podcastName = this.podcastName.value || 'Podcastfy Podcast';
            const shareText = `🎙️ Check out this AI-generated podcast: "${podcastName}" created with Podcastfy!`;
            const shareUrl = this.currentAudioUrl;
            
            // Create a comprehensive share message
            const fullShareText = `${shareText}\n\n🎵 Listen: ${shareUrl}\n\n💡 Created with AI at: ${window.location.origin}`;

            try {
                if (navigator.share && navigator.canShare && navigator.canShare({ url: shareUrl })) {
                    // Use native share API if available
                    await navigator.share({
                        title: podcastName,
                        text: shareText,
                        url: shareUrl
                    });
                } else {
                    // Enhanced fallback with multiple options
                    this.showShareModal(fullShareText, shareUrl, podcastName);
                }
            } catch (error) {
                if (error.name !== 'AbortError') {
                    console.error('Share failed:', error);
                    this.showShareModal(fullShareText, shareUrl, podcastName);
                }
            }
        }
    }

    updateTranscriptStatus(message) {
        // Add or update transcript status indicator
        let statusEl = document.getElementById('transcriptStatus');
        if (!statusEl) {
            statusEl = document.createElement('div');
            statusEl.id = 'transcriptStatus';
            statusEl.className = 'text-xs text-gray-600 mb-2';
            const transcriptSection = document.querySelector('#transcriptContent').parentNode;
            transcriptSection.insertBefore(statusEl, document.querySelector('#transcriptContent'));
        }
        statusEl.textContent = message;
    }

    formatTranscript(transcript) {
        return transcript.replace(/<Person(\d+)>/g, '<span class="font-bold text-blue-600">Person $1:</span>');
    }
}

// Initialize the UI when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new PodcastfyUI();
});
