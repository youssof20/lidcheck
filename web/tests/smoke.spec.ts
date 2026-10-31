import {test,expect} from '@playwright/test';
test('complete check with all network requests blocked after load',async({page})=>{
  await page.goto('./');await page.evaluate(()=>document.fonts.ready);
  const csp=await page.locator('meta[http-equiv="Content-Security-Policy"]').getAttribute('content');expect(csp).toContain("connect-src 'none'");
  const attempted:string[]=[];
  await page.route('**/*',route=>{attempted.push(route.request().url());return route.abort();});
  await page.getByRole('button',{name:'Try a synthetic example'}).click();
  await expect(page.getByRole('heading',{name:'Check the marked area'})).toBeVisible();
  await page.getByRole('button',{name:'Confirm eyelid area'}).click();
  await expect(page.getByText('This is a screening aid, not a diagnosis.',{exact:true})).toBeVisible();
  await expect(page.getByRole('heading',{name:'Clinician summary'})).toBeVisible();
  await expect(page.getByRole('button',{name:'Print summary'})).toBeVisible();
  await page.screenshot({path:'../results/figures/app-synthetic.png',fullPage:true,animations:'disabled'});
  expect(attempted).toEqual([]);
  expect(await page.evaluate(()=>localStorage.length+sessionStorage.length)).toBe(0);
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  await page.getByRole('button',{name:'Retake',exact:true}).click();
  await expect(page.locator('canvas')).toHaveCount(0);
});
test('study mode hides health results and exports measurements',async({page})=>{
  await page.goto('./#study');await page.getByRole('button',{name:'Try a synthetic example'}).click();await page.getByRole('button',{name:'Confirm eyelid area'}).click();
  await page.getByLabel('Participant code').fill('P01');await page.getByLabel('Phone model').fill('Synthetic browser');
  await page.getByRole('button',{name:'Add measurements'}).click();await expect(page.getByText('Measurements added.',{exact:false})).toBeVisible();
  await expect(page.getByRole('button',{name:'Print summary'})).toHaveCount(0);
  const download=page.waitForEvent('download');await page.getByRole('button',{name:'Download study JSON'}).click();expect((await download).suggestedFilename()).toBe('lidcheck-study.json');
});
