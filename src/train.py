import os, json
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.applications import ResNet50
from tensorflow.keras import layers, models, optimizers
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
import tensorflow as tf

# Configure paths
DATA_DIR = os.environ.get('DATA_DIR', '/content/monkeypoxskinimagedataset')  # default for Colab after download
SAVED_MODEL_DIR = os.environ.get('SAVED_MODEL_DIR', './saved_model')
BATCH_SIZE = int(os.environ.get('BATCH_SIZE', 16))
IMG_SIZE = (224,224)
EPOCHS = int(os.environ.get('EPOCHS', 25))

os.makedirs(SAVED_MODEL_DIR, exist_ok=True)

train_datagen = ImageDataGenerator(
    rescale=1./255,
    rotation_range=25,
    width_shift_range=0.12,
    height_shift_range=0.12,
    shear_range=0.12,
    zoom_range=0.12,
    horizontal_flip=True,
    validation_split=0.15
)

train_gen = train_datagen.flow_from_directory(
    DATA_DIR, target_size=IMG_SIZE, batch_size=BATCH_SIZE,
    class_mode='categorical', subset='training', shuffle=True
)
val_gen = train_datagen.flow_from_directory(
    DATA_DIR, target_size=IMG_SIZE, batch_size=BATCH_SIZE,
    class_mode='categorical', subset='validation', shuffle=False
)

num_classes = train_gen.num_classes
labels_map = train_gen.class_indices
print('Found classes:', labels_map)

base = ResNet50(weights='imagenet', include_top=False, input_shape=(*IMG_SIZE,3))
base.trainable = False

x = base.output
x = layers.GlobalAveragePooling2D()(x)
x = layers.Dropout(0.4)(x)
x = layers.Dense(256, activation='relu')(x)
x = layers.Dropout(0.3)(x)
preds = layers.Dense(num_classes, activation='softmax')(x)

model = models.Model(inputs=base.input, outputs=preds)
model.compile(optimizer=optimizers.Adam(1e-4), loss='categorical_crossentropy', metrics=['accuracy'])

checkpoint = ModelCheckpoint(os.path.join(SAVED_MODEL_DIR, 'best_model.h5'), save_best_only=True, monitor='val_accuracy')
es = EarlyStopping(patience=6, restore_best_weights=True, monitor='val_loss')

history = model.fit(train_gen, validation_data=val_gen, epochs=EPOCHS, callbacks=[checkpoint, es])

# Fine-tune last layers
for layer in base.layers[-30:]:
    layer.trainable = True

model.compile(optimizer=optimizers.Adam(1e-5), loss='categorical_crossentropy', metrics=['accuracy'])
history2 = model.fit(train_gen, validation_data=val_gen, epochs=5, callbacks=[checkpoint, es])

# Save final
model.save(os.path.join(SAVED_MODEL_DIR, 'final_model.h5'))

with open(os.path.join(SAVED_MODEL_DIR, 'labels.json'), 'w') as f:
    json.dump(labels_map, f)

print('Training complete. Model saved to', SAVED_MODEL_DIR)
