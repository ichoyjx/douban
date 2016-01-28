# ChangeLog
[Main Page](https://github.com/ichoyjx/douban)

## [NOTE for 1.0 changes]
- Search douban user's photo post within one online activity
- Multithreading pool should not be too large, otherwise
Douban will forbid your IP for a while

## [TODO]
- ~~Add parallel fetching the pages~~
- Expand to search one user's all the posts of each activity
- Use option package
- Add exception handling

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
