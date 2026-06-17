export function initializeConditionChips() {
    const container = document.getElementById('condition_container');
    
    if (!container) return;
    const chips = container.querySelectorAll('.chip');

    chips.forEach(chip => {
        chip.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            this.classList.toggle('selected');

            const selectedChips = Array.from(container.querySelectorAll('.chip.selected'))
            .map(c => c.dataset.value);
            localStorage.setItem('rs_condition_id', JSON.stringify(selectedChips));
        });
    });

    const saved = localStorage.getItem('rs_condition_id');
    if (saved) {
        try {
            const savedIds = JSON.parse(saved);
            chips.forEach(chip => {
                if (savedIds.includes(chip.dataset.value)) {
                    chip.classList.add('selected');
                }
            });
        } catch(e) {
            console.error("Error parsing saved conditions", e);
        }
    }
}



export function getSelectedConditionIds() {
    const container = document.getElementById('condition_container');
    if (!container) return [];
    return Array.from(container.querySelectorAll('.chip.selected')).map(c => c.dataset.value);

}


export default { initializeConditionChips, getSelectedConditionIds }; 