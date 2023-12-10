# Electronic-Music-Assassin
This repository is the core implementation of the black-box audio adversarial attack approach proposed by our paper (Electronic Music Assassin: Towards Imperceptible Physical Adversarial Attacks against Black-box Automatic Speech Recognitions).

# Installation
1.Clone this repo.
```
git clone https://github.com/yzslry/Electronic-Music-Assassin.git
cd Electronic-Music-Assassin
```
2.Create a virtual environment running Python 3.8 interpreter of later.

3.Install the dependencies.
```
pip install -r requirements.txt
```
# Usage
1.Register the target ASR cloud services provided and fill in the relevant information in the  `account.py`.

2.Create the `music` folder and add the song you would like as carrier audios to it in wav format with the sample rate of 16000

3.Use the cloud text-to-speech service to generate audios of the target attack commands in wav format with the sample rate of 16000 and place them under the `command` folder

4.For attacks in the digital world, you can obtain the AEs by executing the following code：
```
python attack_digital.py --speech-file-path target_TTS_path --music-file-path ./music --attack-target [tencentyun,aliyun,iflytec,google,azure] --sample-num successful_AEs_number
```
Successful AEs will be saved in folder `success_digital_samples`

5.For attacks in the physical world, you can obtain the AEs by executing the following code：
```
python attack_physical.py --speech-file-path target_TTS_path --music-file-path ./music --sample-num AEs_number
```
AEs will be saved in folder `physical_samples` and you need the test wheather they are successful in the physical devices.

# Demos
<audio src="https://github.com/yzslry/Electronic-Music-Assassin/blob/main/AEs/digital/ours/call_my_wife.wav"></audio>


