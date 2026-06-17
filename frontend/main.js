import { analyzeFile, fetchInitial, rerank } from './api.js';
import { initializeConditionChips, getSelectedConditionIds } from './chips.js';

let currentPool = [];

function showLoading() { document.getElementById('loading').style.display = 'block'; }
function hideLoading() { document.getElementById('loading').style.display = 'none'; }

function renderGrid(items) {
    const container = document.getElementById('gallery');
    container.innerHTML = '';
    if (!items || !items.length) {
        container.innerHTML = '<div style="grid-column: span 12; text-align:center; color: var(--text-muted); padding: 40px 0;">No matching data layers found in background storage.</div>';
        return;
    }

    items.forEach(item => {
        const card = document.createElement('a');
        card.className = 'product-card';
        card.href = item.url;
        card.target = '_blank';
        const scoreDisplay = item.score ? `<div class="product-score">Match: ${Math.round(item.score * 100)}%</div>` : '';

        card.innerHTML = `
            <img src="${item.image_url}" alt="Listing" loading="lazy">
            <div class="product-info">
                <div class="product-title">${item.title}</div>
                ${scoreDisplay}
            </div>
        `;
        container.appendChild(card);
    });
}

function safeAttachFieldListeners() {
    const fields = ['size_id', 'max_price', 'condition_id'];
    fields.forEach(f => {
        const el = document.getElementById(f);
        if (!el) return;
        const eventType = el.tagName === 'SELECT' ? 'change' : 'input';
        el.value = localStorage.getItem(`rs_${f}`) || '';
        el.addEventListener(eventType, () => localStorage.setItem(`rs_${f}`, el.value));
    });
}

function wireUI() {
    // Image upload -> analyze
    const imageLoader = document.getElementById('image_loader');
    imageLoader.addEventListener('change', async (e) => {
        const file = e.target.files[0];
        if (!file) return;
        showLoading();
        try {
            const data = await analyzeFile(file);
            document.getElementById('confirmed_keyword').value = data.archetype;

            // Build keyword suggestion chips (allows user to pick an alternate keyword)
            const tagsContainer = document.getElementById('suggested_keywords_container');
            if (tagsContainer) {
                tagsContainer.innerHTML = '';
                const rawKeywords = [data.archetype, ...(data.suggested_tags || [])];
                const uniqueKeywords = [...new Set(rawKeywords.filter(k => k && !k.includes('color')))];

                uniqueKeywords.forEach((keyword, index) => {
                    const chip = document.createElement('div');
                    chip.className = `chip ${index === 0 ? 'selected' : ''}`;
                    chip.innerText = keyword;
                    chip.dataset.keyword = keyword;

                    chip.addEventListener('click', function() {
                        document.querySelectorAll('#suggested_keywords_container .chip').forEach(c => c.classList.remove('selected'));
                        this.classList.add('selected');
                        document.getElementById('confirmed_keyword').value = this.dataset.keyword;
                    });

                    tagsContainer.appendChild(chip);
                });

                const suggestionsWrapper = document.getElementById('keyword_suggestions_wrapper');
                if (suggestionsWrapper) suggestionsWrapper.style.display = 'block';
            }

            const sliderContainer = document.getElementById('slider_container');
            sliderContainer.innerHTML = '';

            (data.suggested_tags || []).forEach(tag => {
                const div = document.createElement('div');
                div.className = 'slider-group';
                const defaultVal = (tag.includes('color') || tag === 'dress') ? 0.0 : 0.8;
                div.innerHTML = `
                    <div class="slider-header">
                        <span>${tag}</span>
                        <span id="val_${tag}">${defaultVal}</span>
                    </div>
                    <input type="range" class="weight-slider" data-tag="${tag}" min="0" max="1" step="0.1" value="${defaultVal}">
                `;
                sliderContainer.appendChild(div);
            });

            document.querySelectorAll('.weight-slider').forEach(s => {
                s.addEventListener('input', (ev) => {
                    document.getElementById(`val_${ev.target.dataset.tag}`).innerText = ev.target.value;
                });
            });

            // Close the preference drawer to maximize space for incoming results
            const prefToggle = document.getElementById('pref_toggle_btn');
            const prefContent = document.getElementById('pref_content_panel');
            if (prefToggle) prefToggle.classList.add('open');
            if (prefContent) prefContent.classList.add('show');
        } catch (err) {
            alert('Connection failure to local Python host engine');
        } finally {
            hideLoading();
        }
    });

    // Scrape button
    document.getElementById('trigger_scrape_btn').addEventListener('click', async () => {
        const keywordInput = document.getElementById('confirmed_keyword').value.trim();
        if (!keywordInput) { alert('Please provide or parse a lookup keyword first.'); return; }
        showLoading();
        document.getElementById('slider_panel').classList.remove('active');
        document.getElementById('panel_overlay').style.display = 'none';

        const fetchForm = new FormData();
        fetchForm.append('keyword', keywordInput);
        fetchForm.append('size_id', document.getElementById('size_id').value);
        fetchForm.append('max_price', document.getElementById('max_price').value);
        fetchForm.append('category_name', document.getElementById('category_selector').value);
        fetchForm.append('colour_name', document.getElementById('color_swatch_container').value);

        getSelectedConditionIds().forEach(id => fetchForm.append('condition_id[]', id));

        try {
            const poolData = await fetchInitial(fetchForm);
            currentPool = poolData.pool;
            renderGrid(currentPool);
        } catch (err) {
            alert('Failed fetching items with the chosen keyword.');
        } finally { hideLoading(); }
    });

    // Rerank button
    document.getElementById('rerank_btn').addEventListener('click', async () => {
        if (!currentPool.length) { alert('Run an initial scraping pass before sorting vectors.'); return; }
        showLoading();
        document.getElementById('slider_panel').classList.remove('active');
        document.getElementById('panel_overlay').style.display = 'none';

        const weights = {};
        document.querySelectorAll('.weight-slider').forEach(s => { weights[s.dataset.tag] = parseFloat(s.value); });

        const formData = new FormData();
        formData.append('pool_data', JSON.stringify(currentPool));
        formData.append('weights', JSON.stringify(weights));

        try {
            const rankedData = await rerank(formData);
            renderGrid(rankedData);
        } catch (err) {
            alert('Vector calculation error');
        } finally { hideLoading(); }
    });

    // Pref panel toggle
    document.getElementById('pref_toggle_btn').addEventListener('click', function() {
        this.classList.toggle('open');
        document.getElementById('pref_content_panel').classList.toggle('show');
    });

    // Floating sheet controls
    const fab = document.getElementById('fab_hamburger');
    const panel = document.getElementById('slider_panel');
    const overlay = document.getElementById('panel_overlay');
    const closeBtn = document.getElementById('close_panel');
    function togglePanel() {
        panel.classList.toggle('active');
        overlay.style.display = panel.classList.contains('active') ? 'block' : 'none';
    }
    fab.addEventListener('click', togglePanel);
    closeBtn.addEventListener('click', togglePanel);
    overlay.addEventListener('click', togglePanel);
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    safeAttachFieldListeners();
    initializeConditionChips();
    wireUI();
});

export { renderGrid };
