document.addEventListener("DOMContentLoaded", function() {
    // Find the main "Save" button in the Unfold Admin panel
    const saveBtn = document.querySelector('input[name="_save"], button[name="_save"]');
    
    if (saveBtn) {
        // Clone the Save button so it perfectly inherits all of Unfold's Tailwind CSS classes
        const nextBtn = saveBtn.cloneNode(true);
        
        // Change its properties to trigger our Python logic
        nextBtn.name = '_save_and_next';
        nextBtn.value = 'Save & Next ➔';
        if (nextBtn.tagName.toLowerCase() === 'button') {
            nextBtn.innerHTML = 'Save & Next ➔';
        }
        
        // Make it Green and add a little margin so it stands out!
        nextBtn.style.backgroundColor = '#10b981'; // Emerald Green
        nextBtn.style.borderColor = '#10b981';
        nextBtn.style.marginLeft = '12px';
        
        // Drop it into the page right next to the original Save button
        saveBtn.parentNode.insertBefore(nextBtn, saveBtn.nextSibling);
    }
});