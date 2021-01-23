from os import listdir
from os.path import join
import torch.utils.data as data

from PIL import Image

def is_image_file(filename):
    return any(filename.endswith(extension) for extension in [".png", ".jpg", ".jpeg"])



def load_img(filepath):
    img = Image.open(filepath)
    if len(img.shape) < 3:
        img = np.expand_dims(img, axis=2)
        img = np.repeat(img, 3, axis=2)
    img = imresize(img, (256, 256))
    img = np.transpose(img, (2, 0, 1))
    img = torch.from_numpy(img)
    img = preprocess_img(img)
    return img


class DatasetFromFolder(data.Dataset):
    def __init__(self, image_dir):
        super(DatasetFromFolder, self).__init__()
        self.a_path = join(image_dir, "a")
        self.b_path = join(image_dir, "b")
        self.image_filenames = [x for x in listdir(self.a_path) if is_image_file(x)]

    def __getitem__(self, index):
        # Load Image
        input = load_img(join(self.a_path, self.image_filenames[index]))
        target = load_img(join(self.b_path, self.image_filenames[index]))

        return input, target

    def __len__(self):
        return len(self.image_filenames)
