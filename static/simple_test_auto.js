// Simple Test Automation for Basic Testing
// Copy-paste this into browser console for quick automation

(function() {
    console.log('🤖 Simple Test Automation Loaded');
    
    // Quick fill function - detects current questions and fills them
    function quickFill() {
        console.log('🤖 Quick filling current section...');
        
        // CRT Questions
        const batBall = document.querySelector('input[name="bat_ball"]');
        if (batBall) batBall.value = 0.05;
        
        const widgets = document.querySelector('input[name="widgets"]');
        if (widgets) widgets.value = 5;
        
        const lilyPad = document.querySelector('input[name="lily_pad"]');
        if (lilyPad) lilyPad.value = 47;
        
        // Numeracy Questions
        const diseaseProb = document.querySelector('input[name="disease_prob"]');
        if (diseaseProb) diseaseProb.value = 9.0;
        
        const coinProb = document.querySelector('input[name="coin_prob"]');
        if (coinProb) coinProb.value = 0.5;
        
        // Anchoring Questions
        const moroccoComp = document.querySelector('input[name="morocco_comparison"][value="more"]');
        if (moroccoComp) moroccoComp.checked = true;
        
        const moroccoEst = document.querySelector('input[name="morocco_estimate"]');
        if (moroccoEst) moroccoEst.value = 37;
        
        const companyComp = document.querySelector('input[name="company_comparison"][value="less"]');
        if (companyComp) companyComp.checked = true;
        
        const companyEst = document.querySelector('input[name="company_estimate"]');
        if (companyEst) companyEst.value = 60;
        
        // Intent Questions
        const emailIntent = document.querySelector('input[name="email_intent"][value="neutral"]');
        if (emailIntent) emailIntent.checked = true;
        
        const interruptIntent = document.querySelector('input[name="interrupt_intent"][value="neutral"]');
        if (interruptIntent) interruptIntent.checked = true;
        
        // Radio button groups (Likert scales) - select middle option (3)
        const radioGroups = {};
        document.querySelectorAll('input[type="radio"]').forEach(radio => {
            const name = radio.name;
            if (!radioGroups[name]) radioGroups[name] = [];
            radioGroups[name].push(radio);
        });
        
        Object.values(radioGroups).forEach(group => {
            const middleOption = group.find(r => r.value === '3') || group[Math.floor(group.length/2)];
            if (middleOption) middleOption.checked = true;
        });
        
        console.log('🤖 Questions filled!');
    }
    
    // Auto-advance function
    function clickNext() {
        const selectors = ['#next-btn', 'button[onclick*="next"]', '.btn-primary', 'input[type="submit"]'];
        for (const sel of selectors) {
            const btn = document.querySelector(sel);
            if (btn && btn.offsetParent && !btn.disabled) {
                console.log('🤖 Clicking next...');
                btn.click();
                break;
            }
        }
    }
    
    // Auto-run function
    function autoRun() {
        quickFill();
        setTimeout(clickNext, 1000);
    }
    
    // Make functions globally available
    window.quickFill = quickFill;
    window.clickNext = clickNext;
    window.autoRun = autoRun;
    
    console.log('🤖 Available commands:');
    console.log('  quickFill() - Fill current section');
    console.log('  clickNext() - Click next button');
    console.log('  autoRun() - Fill and advance automatically');
})();