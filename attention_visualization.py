import os
import cv2
import torch
import numpy as np
from PIL import Image
from torchvision import transforms
from vision_transformer import VisionTransformer


class AttentionVisualization:
    def __init__(self):
        self.image = Image.open(os.path.join("data", "sample_input.jpg"))
        self.model = VisionTransformer.from_name("ViT-B_16", num_classes=5)
        self.input_size = (384, 384)
        self.set_transform()

    def visualize(self):
        map = self.get_attention_map(self.image)
        cv2.imshow("map", map)
        cv2.waitKey()

    def set_transform(self):
        self.transform = transforms.Compose(
            [
                transforms.Resize(self.input_size),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406],
                    std=[0.229, 0.224, 0.225],
                ),
            ]
        )

    def get_attention_map(self, img):
        x = self.transform(img)
        _, att_mat = self.model(x.unsqueeze(0))

        att_mat = torch.stack(att_mat).squeeze(1)

        # Average the attention weights across all heads.
        att_mat = torch.mean(att_mat, dim=1)

        # To account for residual connections, we add an identity matrix to the
        # attention matrix and re-normalize the weights.
        residual_att = torch.eye(att_mat.size(1))
        aug_att_mat = att_mat + residual_att
        aug_att_mat = aug_att_mat / aug_att_mat.sum(dim=-1).unsqueeze(-1)

        # Recursively multiply the weight matrices
        joint_attentions = torch.zeros(aug_att_mat.size())
        joint_attentions[0] = aug_att_mat[0]
        for n in range(1, aug_att_mat.size(0)):
            joint_attentions[n] = torch.matmul(aug_att_mat[n], joint_attentions[n - 1])

        v = joint_attentions[-1]
        grid_size = int(np.sqrt(aug_att_mat.size(-1)))
        mask = v[0, 1:].reshape(grid_size, grid_size).detach().numpy()
        mask = cv2.resize(mask / mask.max(), img.size)[..., np.newaxis]
        result = (mask * img).astype("uint8")

        return result

