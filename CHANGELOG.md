# ChangeLog
[Main Page](https://github.com/ichoyjx/douban)

## [NOTE for 1.0 changes]
- ~~Search douban user's photo post within one online activity~~
- Multithreading pool should not be too large, otherwise
Douban will forbid your IP for a while

## [TODO]
- ~~Add parallel fetching the pages~~
- Expand to search one user's all the posts of each activity
- ~~Use option package~~
- Add exception handling

## [1.4.5] - 2016-01-31
### Changed
- Re-structure how to process the photo-wrap: get all the pages
and add them together, then process the entire object to find
the photo-wrap
- Add top option to return the TOP #top images based on the number
of comments
- Add real json format to the project, this will change the way
how we access the photo info and would be easy to do the local
search. For example, the default search method is to check the
existence of json file; it will only recreate the json file if
the -update is present

## [1.3.8] - 2016-01-30
### Changed
- Add options using argparse, probably needs more

## [1.3.6] - 2016-01-29
### Changed
- Add multitheading download images
- **TODO** you don't want to download them everytime, will need
to add a detection to avoid downloading images everytime OR just
let user choose to download them or not. This requires the
options support.

## [1.3.0] - 2016-01-28
### Changed
- Point the direct links to images and save the images to local

## [1.1.6] - 2016-01-28
### Changed
- Add "html.parser" for generic parser
- Wrap more things into functions and for the actual process,
online_id is the only we need for the entry
- Change pool size to 6, save about 30% of elasping time

## [1.0.6] - 2016-01-27
### Changed
- Removed "lxml" since not every environment has parser installed
- Add get\_album\_id to make little bit easier to use
- Add multithreading to fetch the urls (process them later)

## [1.0.0] - 2016-01-26
### First Push to Github
- Init the repo
- Finish the first version, search user's post with album id URL
