from gallerist import Gallerist, ImageSize
from gallerist.fs import FileSystemSyncFileStore


store = FileSystemSyncFileStore('tests')

gallerist = Gallerist(store)


metadata = gallerist.process_image('files/blacksheep.png')


# configuring sizes by mime (use '*' to match any other mime):
gallerist = Gallerist(store, sizes={
    'image/jpeg': [
        ImageSize('a', 500),
        ImageSize('b', 400),
        ImageSize('c', 300)
    ],
    'image/png': [
        ImageSize('a', 350),
        ImageSize('b', 250),
        ImageSize('c', 150)
    ]
})

metadata = gallerist.process_image('files/pexels-photo-126407.jpeg')

print(metadata)
