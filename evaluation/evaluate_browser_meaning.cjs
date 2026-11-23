// Requires Playwright and a running local checkout of the meaning-search PR.
const { chromium } = require('playwright');
const fs = require('node:fs');
const crypto = require('node:crypto');
const path = require('node:path');

const base = process.env.AAYATUN_TEST_URL || 'http://127.0.0.1:19201';
const baseline = JSON.parse(fs.readFileSync(path.join(__dirname, 'semantic_baseline_results.json')));
const cases = Object.entries(baseline.fixtures).flatMap(([name, hash]) => {
    const data = fs.readFileSync(path.join(__dirname, name));
    if (crypto.createHash('sha256').update(data).digest('hex') !== hash) throw new Error(name);
    return data.toString('utf8').trim().split(/\r?\n/).map(line => JSON.parse(line))
        .filter(row => Object.hasOwn(baseline.runs, row.id) && (row.field ?? 'translation') === 'translation');
});

async function main() {
    const browser = await chromium.launch({
        executablePath: process.env.AAYATUN_CHROME || undefined,
    });
    try {
        const page = await browser.newPage();
        page.on('requestfailed', request => console.error(request.failure().errorText, new URL(request.url()).pathname));
        page.on('response', response => {
            if (response.status() >= 400) console.error(response.status(), new URL(response.url()).pathname);
        });
        await page.goto(base + '/static/meaning/index.json');
        await page.evaluate(local => {
            const suffix = local ? '?local-model' : '';
            window.meaningWorker = new Worker('/static/js/meaning-worker.js' + suffix, { type: 'module' });
        }, process.env.AAYATUN_LOCAL_MEANING_MODEL === '1');
        const runs = {};
        const timings = [];
        for (const row of cases) {
            const result = await page.evaluate(query => new Promise((resolve, reject) => {
                const start = performance.now();
                const timer = setTimeout(() => reject(new Error('Meaning worker timed out')), 180000);
                window.meaningWorker.onmessage = ({ data }) => {
                    clearTimeout(timer);
                    if (data.error) reject(new Error('Meaning worker failed'));
                    else resolve({ ...data, ms: Math.round(performance.now() - start) });
                };
                window.meaningWorker.onerror = reject;
                window.meaningWorker.postMessage(query);
            }), row.query);
            runs[row.id] = result.refs;
            timings.push(result.ms);
            if (timings.length === 1 || timings.length % 25 === 0) {
                console.log('Queries', timings.length, 'of', cases.length, 'last milliseconds', result.ms);
            }
        }
        const warm = timings.slice(1).sort((a, b) => a - b);
        const report = {
            model: 'Xenova/multilingual-e5-small',
            model_revision: '761b726dd34fb83930e26aab4e9ac3899aa1fa78',
            dtype: 'int8',
            model_delivery: process.env.AAYATUN_LOCAL_MEANING_MODEL === '1' ? 'static mirror' : 'Hugging Face',
            fixtures: baseline.fixtures, browser: browser.version(), runs,
            first_query_ms: timings[0], warm_p50_ms: warm[Math.floor(warm.length / 2)],
            warm_p95_ms: warm[Math.ceil(warm.length * 0.95) - 1],
        };
        fs.writeFileSync(path.join(__dirname, 'semantic_browser_results.json'),
            JSON.stringify(report, null, 2) + '\n');
    } finally {
        await browser.close();
    }
}

main().catch(error => {
    console.error(error);
    process.exitCode = 1;
});
