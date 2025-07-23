async function askStoic() {
    const input = document.getElementById("questionInput");
    const question = input.value.trim();
    const answerBox = document.getElementById("answerBox");
    const loadingIndicator = document.getElementById('loadingIndicator');

    if (!question) {
        answerBox.textContent = "Please share what troubles you, so that wisdom may guide you.";
        return;
    }

    // Show loading state
    loadingIndicator.classList.add('active');
    answerBox.style.opacity = '0.5';
    answerBox.textContent = "Contemplating wisdom...";

    try {
        const response = await fetch("http://127.0.0.1:5000/ask", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ question })
        });

        const data = await response.json();
        
        // Hide loading state
        loadingIndicator.classList.remove('active');
        answerBox.style.opacity = '1';
        
        if (data.answer) {
            answerBox.textContent = data.answer;
        } else {
            answerBox.textContent = data.error || "No wisdom received at this time.";
        }
        
        // Don't clear the input automatically - let user clear manually with dustbin icon
        
    } catch (err) {
        // Hide loading state
        loadingIndicator.classList.remove('active');
        answerBox.style.opacity = '1';
        answerBox.textContent = "An error occurred. Please try again.";
        console.error(err);
    }
}

// Function to clear the input when dustbin icon is clicked
function clearInput() {
    const input = document.getElementById('questionInput');
    input.value = '';
    input.focus();
    
    // Reset textarea height
    input.style.height = 'auto';
}

const menuIcon = document.getElementById('menuIcon');
const dropdownMenu = document.getElementById('dropdownMenu');

menuIcon.addEventListener('click', function(e) {
    e.stopPropagation();
    menuIcon.classList.toggle('active');
    dropdownMenu.classList.toggle('show');
});

// Close menu when clicking outside
document.addEventListener('click', function(e) {
    if (!menuIcon.contains(e.target) && !dropdownMenu.contains(e.target)) {
        menuIcon.classList.remove('active');
        dropdownMenu.classList.remove('show');
    }
});

// Download functionality
function showNotification(message) {
    const notification = document.getElementById('downloadNotification');
    notification.textContent = message;
    notification.classList.add('show');
    
    setTimeout(() => {
        notification.classList.remove('show');
    }, 3000);
}

// Helper function to prepare element for screenshot
function prepareForScreenshot() {
    const textarea = document.getElementById('questionInput');
    const inputDisplay = document.getElementById('inputDisplay');
    const clearButton = document.querySelector('.clear-button');
    
    // Get the textarea value
    const textareaValue = textarea.value;
    
    // If textarea has content, show it in the display div and hide textarea
    if (textareaValue.trim()) {
        inputDisplay.textContent = textareaValue;
        inputDisplay.style.display = 'block';
        textarea.style.display = 'none';
        // Hide clear button during screenshot
        if (clearButton) clearButton.style.display = 'none';
    }
    
    return { textarea, inputDisplay, clearButton, hasContent: textareaValue.trim() !== '' };
}

// Helper function to restore elements after screenshot
function restoreAfterScreenshot(elements) {
    const { textarea, inputDisplay, clearButton, hasContent } = elements;
    
    // Restore original state
    if (hasContent) {
        inputDisplay.style.display = 'none';
        textarea.style.display = 'block';
        if (clearButton) clearButton.style.display = 'block';
    }
}

function generateRandomScribbles(count1 = 50, count2 = 50, minPadding = 50) {
    const body = document.body;
    const placedBoxes = [];
    const boxSize = 120; 
    const maxAttempts = 200;

    function getRandomPosition() {
        return {
            top: Math.random() * (window.innerHeight - boxSize),
            left: Math.random() * (window.innerWidth - boxSize)
        };
    }

    function doesOverlap(newBox) {
        for (const box of placedBoxes) {
            const horizontallyApart = newBox.left + boxSize + minPadding < box.left ||
                                      box.left + boxSize + minPadding < newBox.left;
            const verticallyApart = newBox.top + boxSize + minPadding < box.top ||
                                    box.top + boxSize + minPadding < newBox.top;
            if (!(horizontallyApart || verticallyApart)) return true;
        }
        return false;
    }

    function placeScribble(typeClass) {
        let attempts = 0;
        let pos;

        do {
            pos = getRandomPosition();
            attempts++;
        } while (doesOverlap(pos) && attempts < maxAttempts);

        if (attempts >= maxAttempts) return;

        const el = document.createElement('div');
        el.classList.add('scribble', typeClass);
        el.style.top = `${pos.top}px`;
        el.style.left = `${pos.left}px`;
        el.style.transform = `rotate(${Math.floor(Math.random() * 360)}deg)`;

        placedBoxes.push(pos);
        body.appendChild(el);
    }

    for (let i = 0; i < count1; i++) placeScribble('scribble1');
    for (let i = 0; i < count2; i++) placeScribble('scribble2');
}

window.addEventListener('DOMContentLoaded', () => {
    generateRandomScribbles(20, 20, 50); // Total 40 scribbles with 50px safe spacing
});

async function downloadStoicResponse() {
    try {
        const responsePanel = document.getElementById('responsePanel');
        if (!responsePanel) {
            showNotification('Response panel not found. Please try again.');
            return;
        }

        // Check if html2canvas is loaded
        if (typeof html2canvas === 'undefined') {
            showNotification('Screenshot library not loaded. Please refresh the page.');
            return;
        }

        // Wait for fonts to load
        await document.fonts.ready;

        const canvas = await html2canvas(responsePanel, {
            backgroundColor: "#b8935f",
            scale: 2,
            useCORS: true,
            allowTaint: true,
            letterRendering: true,
            logging: false
        });
        
        const link = document.createElement('a');
        link.download = `stoic-response-${new Date().toISOString().slice(0, 10)}.png`;
        link.href = canvas.toDataURL();
        link.click();
        
        showNotification('Stoic response downloaded successfully!');
        
        // Close menu
        menuIcon.classList.remove('active');
        dropdownMenu.classList.remove('show');
    } catch (error) {
        console.error('Error capturing screenshot:', error);
        showNotification('Error downloading screenshot. Please try again.');
    }
}

async function downloadFullScreenshot() {
    // Close menu first before taking screenshot
    menuIcon.classList.remove('active');
    dropdownMenu.classList.remove('show');
    
    // Wait for fonts to load
    await document.fonts.ready;
    
    try {
        const screen = document.querySelector('.screen');
        if (!screen) {
            showNotification('Screen element not found. Please try again.');
            return;
        }

        // Check if html2canvas is loaded
        if (typeof html2canvas === 'undefined') {
            showNotification('Screenshot library not loaded. Please refresh the page.');
            return;
        }

        // Prepare elements for screenshot
        const elementStates = prepareForScreenshot();

        // Small delay to ensure DOM is updated and menu is fully closed
        await new Promise(resolve => setTimeout(resolve, 200));

        const canvas = await html2canvas(screen, {
            backgroundColor: null,
            scale: 2,
            useCORS: true,
            allowTaint: true,
            letterRendering: true,
            logging: false,
            onclone: function(clonedDoc) {
                // Ensure proper text rendering in cloned document
                const clonedInputDisplay = clonedDoc.getElementById('inputDisplay');
                const clonedTextarea = clonedDoc.getElementById('questionInput');
                
                if (clonedInputDisplay && clonedTextarea) {
                    clonedInputDisplay.style.whiteSpace = 'pre-wrap';
                    clonedInputDisplay.style.wordWrap = 'break-word';
                    clonedInputDisplay.style.overflowWrap = 'break-word';
                    clonedInputDisplay.style.wordBreak = 'break-word';
                }
            }
        });
        
        // Restore elements after screenshot
        restoreAfterScreenshot(elementStates);
        
        const link = document.createElement('a');
        link.download = `stoic-companion-screenshot-${new Date().toISOString().slice(0, 10)}.png`;
        link.href = canvas.toDataURL();
        link.click();
        
        showNotification('Full screenshot downloaded successfully!');
        
    } catch (error) {
        console.error('Error capturing screenshot:', error);
        showNotification('Error downloading screenshot. Please try again.');
        
        // Make sure to restore elements even if there's an error
        try {
            const elementStates = prepareForScreenshot();
            restoreAfterScreenshot(elementStates);
        } catch (restoreError) {
            console.error('Error restoring elements:', restoreError);
        }
    }
}

// Allow Enter key to submit (with Shift+Enter for new line)
document.getElementById('questionInput').addEventListener('keydown', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        askStoic();
    }
});

// Auto-resize textarea
document.getElementById('questionInput').addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = Math.min(this.scrollHeight, 300) + 'px';
});


document.querySelector('.back-arrow').addEventListener('click', function() {
    // Add your back navigation logic here
    console.log('Back arrow clicked');
});

document.querySelector('.menu-icon').addEventListener('click', function() {
    // Add your menu logic here
    console.log('Menu icon clicked');
});