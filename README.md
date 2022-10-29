# Subtitling Copilot

First repository of the subtitling copilot. Currently working, but to be replaced with a cleaner, better version. Started as a group of functions to help with subtitling work, but became a desktop application for better use.

## Features

### OST

- Extract OST

![image](https://user-images.githubusercontent.com/60672110/198849584-a6486abb-c86f-46e0-afce-19dd365de168.png)

Specifically created for the MasterClass project but used in other projects.

Extracts the on-screen text captions from WebVTT files that are raised to the top of the screen (default to 20%), start with '[' and end with ']' and have text in all caps. The user has the option to save the new WebVTT files from the extracted OST and/or delete them from the original files.

<br>

- Merge OST

![image](https://user-images.githubusercontent.com/60672110/198849743-a66a1278-2627-4254-90f0-c9bc73a32468.png)

Specifically created for the MasterClass project but used in other projects.

Merges OST files with audio subtitle files in batch. The files can be dropped into the fields and the program will sort them using OS sorting. Has the option to overwrite the subtitle files or create new ones in a specified directory.

<br>

- Generate OST

![image](https://user-images.githubusercontent.com/60672110/198849820-91c94426-d2ce-4144-a78f-159c41589b2b.png)

Specifically created for the MasterClass project.


Receives a list of .docx OST audit files, reads them and automatically generates WebVTT files, saving them in the specified directory.

<br>

### Batch Quality Check

Runs a quality check on subtitle files, currently only .srt and .vtt, with the option to change limits. Changes to 'Results' tab automatically to show the report after the quality check has been run.

![image](https://user-images.githubusercontent.com/60672110/198850810-5ef41c1c-5be3-4bfd-8078-5043a19298b1.png)


![image](https://user-images.githubusercontent.com/60672110/198850100-91f77882-7cb6-4c09-8e33-35782a4eb97e.png)



Available settings:

- Characters per second (including or excluding spaces)
- Characters per line
- Maximum number of lines
- Minimum duration
- Maximum duration
- Check three dots instead of ellipses
- Gaps
- Timing to shot changes (uses binary search to improve efficiency when finding shot changes near in or out cues)
- Check if text can fit in one line
- Checks Netflix glyph list
- Check OST (addition for the MasterClass project and similar ones)

Can generate a report in a .txt file or show it in the 'Results' tab.


### Issues

Specifically created for the Masterclass project, but can be used for any project in which the subtitling and translation tasks are performed by different teams. Receives the list of source language files and the list of target language files. Finds reading-speed and characters-per-line issues and creates a spreadsheet with the offending segments in the target language, along with surrounding sentences for context and the source text in the same time span. Used for translators to fix issues so subtitlers could implement the fixes.

![image](https://user-images.githubusercontent.com/60672110/198850238-490933b0-c6d4-4bc3-961b-9266f14d3c8f.png)


### Fixes

Implements automatic fixes according to the settings used.

Available settings:

- Snap to frames. When timing to shot changes and controlling gaps in files that can only use media timecodes (HH:MM:SS.mmm), it is better to snap all the times to the frames to which they correspond so avoid false positives.
- Text can fit in one line
- Close gaps. For example, when working with videos of 24 fps, any gap that is between 3 and 11 frames is brought to 2 frames.
- Apply minimum gaps. Takes any gap of 0 or 1 frame to 2 frames.
- Fix invalid italic tags. Showed as an option, but it is always automatically done when parsing VTT files at least.
- Fix unused line breaks.
- Flag empty subtitles. Not deleted, just flagged so the user can check them.
- Sort by start time. WebVTT files cannot work correctly in web players if they are not sorted by start time.

![image](https://user-images.githubusercontent.com/60672110/198850427-91f1b8d9-ed34-4a1d-ae59-8c37b15ac6ba.png)

<br>

### Utilities

Options:

- Copy shot changes

Subtitle Edit uses a hash to name scene/shot changes files. After "cleaning" them, if they need to be shared, it is too tedious to find the corresponding files. This option finds them all automatically by receiving the videos in the field and copies the scene/shot changes files to the specified directory. They can then be shared easily.

![image](https://user-images.githubusercontent.com/60672110/198850516-6d0f0275-0874-4646-81ce-d368c786a345.png)


- Generate shot changes

This can be done in batch with Subtitle Edit, but the sensitivity is limited for videos with dark images. This feature allows the user to set the sensitivity to any value allowed by FFmpeg.

![image](https://user-images.githubusercontent.com/60672110/198850555-6cb5f2d5-61ef-4111-a77c-b24384dfa388.png)


- Frame rates

Since the settings in subtitle editors will depend on frame rates, this shows the frame rates of any batch of videos so the user knows them all before starting work.

![image](https://user-images.githubusercontent.com/60672110/198850587-d2634f87-d918-47c9-b799-0f4b6cae717c.png)


- Statistics

Currently shows total CPS (with and without spaces) and total words. The calculation for total words uses the [Memsource method](https://support.phrase.com/hc/en-us/articles/5709712007708-Analysis-TMS-).

![image](https://user-images.githubusercontent.com/60672110/198850735-04249125-1f58-4035-b734-63c6bf4c88ba.png)


- Converters

Not complete yet. Only created for a request to convert to JSON.

![image](https://user-images.githubusercontent.com/60672110/198850759-8d672b02-706c-4f4a-a064-fda4169f284f.png)
