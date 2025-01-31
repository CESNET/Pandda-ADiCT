<div align="center">
<picture>
  <source srcset="https://raw.githubusercontent.com/CESNET/Pandda-ADiCT/refs/heads/main/img/logo_horizontal_white.svg" media="(prefers-color-scheme: dark)">
  <img src="https://raw.githubusercontent.com/CESNET/Pandda-ADiCT/refs/heads/main/img/logo_horizontal_black.svg">
</picture>
</div>

PANDDA-ADiCT is a streamlined version of CESNET's Asset Discovery, Classification, and Tagging (ADiCT) system. It provides a lightweight yet powerful approach to asset discovery and classification using modular components.

## Project Structure
```
dp3_server/ – Contains the configuration and additional modules for PANDDA-ADiCT.
nemea_modules/ – Hosts the input data collector modules based on the NEMEA framework.
fronted/ - webapp in vue.js presenting the asset discovery results 
```

##  Installation & Usage
This repository is intedet to be used with PANDDA infrastructure. Here are other PANDDA:
* https://github.com/CESNET/Pandda-Playbooks/

Clone the repository:
```
git clone https://github.com/CESNET/Pandda-ADiCT.git
cd Pandda-ADiCT
```