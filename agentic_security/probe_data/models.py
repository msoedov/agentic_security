import os
from dataclasses import dataclass

from tqdm import tqdm


@dataclass
class ProbeDataset:
    dataset_name: str
    metadata: dict
    prompts: list[str]
    tokens: int
    approx_cost: float
    lazy: bool = False

    def metadata_summary(self):
        return {
            "dataset_name": self.dataset_name,
            "num_prompts": len(self.prompts),
            "tokens": self.tokens,
            "approx_cost": self.approx_cost,
        }


@dataclass
class ImageProbeDataset:
    test_dataset: ProbeDataset
    image_prompts: list[bytes]

    def save_images(self, output_dir: str):
        os.makedirs(output_dir, exist_ok=True)
        for index, image_data in enumerate(
            tqdm(self.image_prompts, desc="Saving images")
        ):
            file_path = os.path.join(output_dir, f"image_{index}.png")
            with open(file_path, "wb") as image_file:
                image_file.write(image_data)
