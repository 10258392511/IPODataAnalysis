# Custom GPTs for Industry and IPO Analysis

This directory contains prompts for two custom GPTs developed using OpenAI. The custom GPTs are designed in Chinese, but prompts in both Chinese and English versions are available here for convenience. To get an overview of the main inputs for a target company, visit [this page](http://listing.szse.cn/projectdynamic/ipo/detail/index.html?id=1003162).

## 1. Industry and Company Analyst GPT

This GPT is designed to assist industry and company analysts, specifically for use within an investment bank. It follows the guidelines outlined in the document **Industry Analysis GPT Setup - Roles and Preliminary Instructions.pdf** and answers key questions as per **Guidelines for Industry Insights.pdf**.
   
- **Main Input**: The latest prospectus of the target company, such as [this prospectus](https://reportdocs.static.szse.cn/UpFiles/rasinfodisc1/202406/RAS_202406_3000058B49907146424563AC118D4F3481508E.pdf) for Sinomune Pharmaceutical Co., Ltd.

## 2. CSRC Pre-reviewer GPT

The second GPT is tailored for pre-reviewers working at the China Securities Regulatory Commission (CSRC). It follows the guidelines from **Pre-reviewer Custom GPT Setup - Roles and Preliminary Instructions.pdf** and generates questions related to the target company’s prospectus, which must be answered by the sponsor, reporting accountant, and/or the issuer's legal counsel.

- **Main Inputs**:
   1. Prospectuses and inquiry letters of companies preparing for IPO within the same sector as the training set. The custom GPT learns to map the prospectuses to relevant inquiry questions. An example of the inquery letter for Sinomune Pharmaceutical Co., Ltd. can be found [here](http://reportdocs.static.szse.cn/UpFiles/rasinfodisc1/202403/RAS_202403_151920579AB4ED2E4F42799AC3A0C6C3B5C406.pdf).
   2. The target company’s prospectus is used as the input for inference.
   3. **Data Tree.pdf** is used to attribute each question.
